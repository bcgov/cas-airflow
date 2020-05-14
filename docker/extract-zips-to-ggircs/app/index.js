const argv = require('yargs').argv;
const unzipperDirectory = require('unzipper/lib/Open/directory');
const {Storage} = require('@google-cloud/storage');
const chardet = require('chardet');
const pg = require('pg');
const md5 = require('md5');

const pgPool = new pg.Pool(); // Uses libpq env variables for connection information
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
      await processZipFile(zipFile, zipPasswords);
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

      await processZipFile(file, zipPasswords);
    }
  }
})().catch((error) => console.error(error.stack));

async function processZipFile(zipFile, zipPasswords, passwordIndex = 0) {
  let shouldTryNextPassword = false;
  const metadata = await zipFile.getMetadata();
  const zipFileMd5 = Buffer.from(metadata[0].md5Hash, 'base64').toString('hex');
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
      // There's still some memory leak somewhere, and it it quite slow.
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

  const directory = await unzipperDirectory(directorySource, {crx: true});
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
        const encoding = chardet.detect(xmlReportBuffer);
        const xmlReportMd5 = md5(xmlReportBuffer);
        await pgClient.query(
          `insert into swrs_extract.eccc_xml_file(xml_file, xml_file_name, xml_file_md5_hash, zip_file_id)
          values ($1, $2, $3, $4)
          on conflict(xml_file_md5_hash) do update set
          xml_file=excluded.xml_file,
          xml_file_name=excluded.xml_file_name,
          zip_file_id=excluded.zip_file_id
          `,
          [
            xmlReportBuffer.toString(encoding).replace(/\0/g, ''),
            file.path,
            xmlReportMd5,
            zipFileId
          ]
        );
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
    } else throw error;
  } finally {
    pgClient.release();
  }

  if (shouldTryNextPassword)
    await processZipFile(zipFile, zipPasswords, passwordIndex + 1);
}

/* eslint-enable no-await-in-loop */
