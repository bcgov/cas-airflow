// Const Minio = require('minio');
const argv = require('yargs').argv;
const unzipper = require('unzipper');
const unzipperDirectory = require('unzipper/lib/Open/directory');
const etl = require('etl');
const {Storage} = require('@google-cloud/storage');
const fs = require('fs');

// Creates a client
const storage = new Storage({keyFilename: 'gcs_key.json'});

// Const MINIO_ACCESS_KEY = argv.minio_access_key || process.env.MINIO_ACCESS_KEY;
// const MINIO_SECRET_KEY = argv.minio_secret_key || process.env.MINIO_SECRET_KEY;
// const MINIO_PORT =
//   argv.minio_port ||
//   (process.env.MINIO_PORT && Number.parseInt(process.env.MINIO_PORT, 10));
// const MINIO_SSL = argv.minio_ssl || process.env.MINIO_SSL === 'true';
// const MINIO_HOST = argv.minio_host || process.env.MINIO_HOST;
const DOWNLOAD_ECCC_FILES_XCOM = JSON.parse(
  argv.download_eccc_files_xcom || process.env.DOWNLOAD_ECCC_FILES_XCOM
);

// Const minioClient = new Minio.Client({
//   endPoint: MINIO_HOST,
//   port: MINIO_PORT,
//   useSSL: MINIO_SSL,
//   accessKey: MINIO_ACCESS_KEY,
//   secretKey: MINIO_SECRET_KEY
// });

(async function () {
  for (const {
    bucketName,
    objectName
  } of DOWNLOAD_ECCC_FILES_XCOM.uploadedObjects) {
    const zipFile = storage.bucket(bucketName).file(objectName);
    const directorySource = {
      async size() {
        const metadata = await zipFile.getMetadata();
        console.log(metadata[0].size);
        return metadata[0].size;
      },
      stream(offset, length) {
        console.log(offset, length, offset + length);
        return zipFile.createReadStream({
          start: offset,
          end: length && offset + length
        });
      }
    };
    const directory = await unzipperDirectory(directorySource, {crx: true});
    directory.files.forEach((f) => console.log(f.path));
    // Const objectStream = storage
    //   .bucket(bucketName)
    //   .file(objectName)
    //   .createReadStream();
    // objectStream.pipe(unzipper.Open.s3()).pipe(
    //   etl.map((entry) => {
    //     console.log(entry.path);
    //     entry.autodrain();
    //   })
    // );
  }
})();
