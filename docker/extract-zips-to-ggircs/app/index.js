const argv = require('yargs').argv;
const unzipperDirectory = require('unzipper/lib/Open/directory');
const fs = require('fs');
const {Storage} = require('@google-cloud/storage');
const {pipeline} = require('stream');
const pg = require('pg');

const storage = new Storage({keyFilename: 'gcs_key.json'});

const DOWNLOAD_ECCC_FILES_XCOM =
  argv.download_eccc_files_xcom || process.env.DOWNLOAD_ECCC_FILES_XCOM;

const ECCC_ZIP_PASSWORDS =
  argv.eccc_zip_passwords || process.env.ECCC_ZIP_PASSWORDS;

/* eslint-disable no-await-in-loop */
(async function () {
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
})();

async function processZipFile(zipFile, zipPasswords, passwordIndex = -1) {
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

  try {
    const directory = await unzipperDirectory(directorySource, {crx: true});
    for (const file of directory.files) {
      if (file.path.toLowerCase().endsWith('.xml')) {
        console.log(`Streaming ${file.path}`);
        await streamFile(file, password);
      } else {
        console.log(`Skipping ${file.path}`);
      }
    }
  } catch (error) {
    if (error.message === 'MISSING_PASSWORD') {
      console.log(`${zipFile.name} needs a password`);
    } else if (error.message === 'BAD_PASSWORD') {
      console.log(
        `${zipFile.name} failed to open with password #${passwordIndex + 1}`
      );
    } else throw error;

    processZipFile(zipFile, zipPasswords, passwordIndex + 1);
  }
}

function streamFile(file, password) {
  return new Promise((resolve, reject) => {
    pipeline(file.stream(password), fs.createWriteStream(file.path), (err) => {
      if (err) reject(err);
      else resolve();
    });
  });
}

/* eslint-enable no-await-in-loop */
