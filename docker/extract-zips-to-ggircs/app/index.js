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

  const ECCC_ZIP_PASSWORDS =
    argv.eccc_zip_passwords || process.env.ECCC_ZIP_PASSWORDS;
  if (!DOWNLOAD_ECCC_FILES_XCOM) {
    console.log('DOWNLOAD_ECCC_FILES_XCOM env variable is required');
    return;
  }

  if (!ECCC_ZIP_PASSWORDS) {
    console.log('ECCC_ZIP_PASSWORDS env variable is required');
    return;
  }

  const {uploadedObjects} = JSON.parse(DOWNLOAD_ECCC_FILES_XCOM);
  const zipPasswords = JSON.parse(ECCC_ZIP_PASSWORDS);
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
})().catch((error) => console.error(error.stack));

async function processZipFile(zipFile, zipPasswords, passwordIndex = -1) {
  let shouldTryNextPassword = false;
  const metadata = await zipFile.getMetadata();
  const zipFileMd5 = Buffer.from(metadata[0].md5Hash, 'base64').toString('hex');
  const directorySource = {
    async size() {
      const metadata = await zipFile.getMetadata();
      return metadata[0].size;
    },
    stream(offset, length) {
      return zipFile.createReadStream({
        start: offset,
        end: length && offset + length
      });
    }
  };
  let password;
  if (passwordIndex === -1) {
    console.log(`Opening ${zipFile.name} without password `);
  } else if (passwordIndex >= zipPasswords.length) {
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
    await pgClient.query('begin');

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
        const xmlReportBuffer = await streamFile(file, password);
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
            xmlReportBuffer.toString(encoding),
            file.path,
            xmlReportMd5,
            zipFileId
          ]
        );
      } else {
        console.log(`Skipping ${file.path}`);
      }
    }

    await pgClient.query('commit');
  } catch (error) {
    await pgClient.query('rollback');
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

function streamFile(file, password) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    file
      .stream(password)
      .on('error', reject)
      .on('data', (chunk) => chunks.push(chunk))
      .on('end', () => {
        const buffer = Buffer.concat(chunks);
        resolve(buffer);
      });
  });
}

/* eslint-enable no-await-in-loop */
