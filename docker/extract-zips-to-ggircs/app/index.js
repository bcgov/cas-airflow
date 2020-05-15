const argv = require('yargs').argv;
const unzipperDirectory = require('unzipper/lib/Open/directory');
const {Open} = require('unzipper');
const {Storage} = require('@google-cloud/storage');
const chardet = require('chardet');
const pg = require('pg');
const md5 = require('md5');
const fs = require('fs');

const pgPool = new pg.Pool(); // Uses libpq env variables for connection information
const TMP_ZIP_DESTINATION =
  argv.tmp_zip_destination || process.env.TMP_ZIP_DESTINATION;

/* eslint-disable no-await-in-loop */
(async function () {
  if (!process.env.GCS_KEY) {
    console.log('GCS_KEY env variable is required');
    return;
  }

  const {projectId, client_email, private_key} = JSON.parse(
    process.env.GCS_KEY
  );

  const storage = new Storage({
    projectId,
    credentials: {
      client_email,
      private_key
    }
  });

  const DOWNLOAD_ECCC_FILES_XCOM =
    argv.download_eccc_files_xcom || process.env.DOWNLOAD_ECCC_FILES_XCOM;

  const GCS_BUCKET = argv.gcs_bucket || process.env.GCS_BUCKET;

  const ECCC_ZIP_PASSWORDS =
    argv.eccc_zip_passwords || process.env.ECCC_ZIP_PASSWORDS;

  const STREAM_FILES = argv.stream_files || process.env.STREAM_FILES === 'true';

  if (!ECCC_ZIP_PASSWORDS) {
    console.log('ECCC_ZIP_PASSWORDS env variable is required');
    return;
  }

  const zipPasswords = JSON.parse(ECCC_ZIP_PASSWORDS);

  if (DOWNLOAD_ECCC_FILES_XCOM) {
    console.log('processing files listed in DOWNLOAD_ECCC_FILES_XCOM');
    const {uploadedObjects} = JSON.parse(DOWNLOAD_ECCC_FILES_XCOM);

    for (const {bucketName, objectName} of uploadedObjects) {
      if (!objectName || !bucketName) continue;
      if (!objectName.endsWith('.zip')) {
        console.log(
          `${objectName} was uploaded in the bucket ${bucketName}, but that doesn't look like a zip file. Skipping.`
        );
        continue;
      }

      const zipFile = storage.bucket(bucketName).file(objectName);
      if (!STREAM_FILES) {
        await zipFile.download({destination: TMP_ZIP_DESTINATION});
      }

      await processZipFile(zipFile, zipPasswords, STREAM_FILES);
    }
  } else if (GCS_BUCKET) {
    console.log('Processing all zip files in gcs bucket');
    const files = await storage.bucket(GCS_BUCKET).getFiles();
    for (const file of files[0]) {
      if (!file.name.endsWith('.zip')) {
        console.log(
          `${file.name} was uploaded in the bucket ${file.name}, but that doesn't look like a zip file. Skipping.`
        );
        continue;
      }

      if (!STREAM_FILES) {
        await file.download({destination: TMP_ZIP_DESTINATION});
      }

      await processZipFile(file, zipPasswords, STREAM_FILES);
    }
  }

  if (!STREAM_FILES) {
    fs.unlinkSync(TMP_ZIP_DESTINATION);
  }
})().catch((error) => {
  throw error;
});

async function processZipFile(
  zipFile,
  zipPasswords,
  streamFile = false,
  passwordIndex = 0
) {
  let shouldTryNextPassword = false;
  const metadata = await zipFile.getMetadata();
  const zipFileMd5 = Buffer.from(metadata[0].md5Hash, 'base64').toString('hex');
  let password;
  if (passwordIndex === zipPasswords.length) {
    console.log(`Opening ${zipFile.name} without password `);
  } else if (passwordIndex > zipPasswords.length) {
    throw new Error(
      `Tried all passwords to open ${zipFile.name}, but none worked.`
    );
  } else {
    console.log(`Opening ${zipFile.name} with password #${passwordIndex + 1}`);
    password = zipPasswords[passwordIndex];
  }

  let directory;
  if (streamFile) {
    const directorySource = {
      async size() {
        const metadata = await zipFile.getMetadata();
        return metadata[0].size;
      },
      stream(offset, length) {
        const readStream = zipFile
          .createReadStream({
            start: offset,
            end: length && offset + length
          })
          .on('end', () => console.log('stream ended'));

        // This could reduce a memory leak by reading the stream.
        // There's still some memory leak somewhere, and it is quite slow.
        // The memory leak is caused by unzipper not finishing to read the stream
        // readStream.abort = () => {
        //   readStream.unpipe();
        //   readStream.on('readable', () => {
        //     while (readStream.read() !== null) {
        //       //console.log(`Received ${chunk.length} bytes of data.`);
        //     }
        //   });
        // };

        return readStream;
      }
    };
    directory = await unzipperDirectory(directorySource);
  } else {
    directory = await Open.file(TMP_ZIP_DESTINATION);
  }

  const pgClient = await pgPool.connect();
  try {
    const insertZipFileResult = await pgClient.query(
      `insert into swrs_extract.eccc_zip_file(zip_file_name, zip_file_md5_hash)
      values ($1, $2)
      on conflict(zip_file_md5_hash) do update set zip_file_name=excluded.zip_file_name
      returning id`,
      [zipFile.name, zipFileMd5]
    );
    const zipFileId = insertZipFileResult.rows[0].id;

    for (const file of directory.files) {
      if (file.path.toLowerCase().endsWith('.xml')) {
        console.log(`Streaming ${file.path}`);
        const xmlReportBuffer = await file.buffer(password);
        const xmlReportMd5 = md5(xmlReportBuffer);
        let encoding;
        let xmlReportString;
        try {
          encoding = chardet.detect(xmlReportBuffer);
          xmlReportString = xmlReportBuffer
            .toString(encoding)
            .replace(/\0/g, '');
        } catch (error) {
          console.error(
            `Failed to decode file ${file.path} from ${zipFile.name} with encoding ${encoding}`
          );
          console.error(error);
          continue;
        }

        try {
          await pgClient.query(
            `insert into swrs_extract.eccc_xml_file(xml_file, xml_file_name, xml_file_md5_hash, zip_file_id)
          values ($1, $2, $3, $4)
          on conflict(xml_file_md5_hash) do update set
          xml_file=excluded.xml_file,
          xml_file_name=excluded.xml_file_name,
          zip_file_id=excluded.zip_file_id
          `,
            [xmlReportString, file.path, xmlReportMd5, zipFileId]
          );
        } catch (error) {
          console.error(error);
          continue;
        }
      } else {
        console.log(`Skipping ${file.path}`);
      }
    }
  } catch (error) {
    if (error.message === 'MISSING_PASSWORD') {
      console.log(`${zipFile.name} needs a password`);
      shouldTryNextPassword = true;
    } else if (error.message === 'BAD_PASSWORD') {
      console.log(
        `${zipFile.name} failed to open with password #${passwordIndex + 1}`
      );
      shouldTryNextPassword = true;
    } else console.error(error);
  } finally {
    pgClient.release();
  }

  if (shouldTryNextPassword)
    await processZipFile(zipFile, zipPasswords, streamFile, passwordIndex + 1);
}

/* eslint-enable no-await-in-loop */
