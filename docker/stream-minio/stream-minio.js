const path = require('path');
const Minio = require('minio');
const argv = require('yargs').argv;
const fs = require('fs');

const fetch = {
  'http:': require('http'),
  'https:': require('https'),
};

const END_POINT = argv.host || process.env.MINIO_HOST;
const PORT = argv.port || (process.env.MINIO_PORT && parseInt(process.env.MINIO_PORT, 10));
const SSL = argv.ssl || process.env.MINIO_SSL === 'true';
const ACCESS_KEY = argv.access_key || process.env.MINIO_ACCESS_KEY;
const SECRET_KEY = argv.secret_key || process.env.MINIO_SECRET_KEY;
const BUCKET_NAME = argv.bucket;
const REGION = argv.region || 'northamerica-northeast1'; // Montreal
const FILE_URLS = Array.isArray(argv.url) ? argv.url : (argv.url && [argv.url]) || [];
const USER = process.env.USER;
const PASSWORD = process.env.PASSWORD;
const XCOM_FILE = '/airflow/xcom/return.json';

if (FILE_URLS.length === 0) {
  console.error('at least one url required');
  return;
}

const httpOption = (USER && PASSWORD && { auth: `${USER}:${PASSWORD}` }) || {};

const minioClient = new Minio.Client({
  endPoint: END_POINT,
  port: PORT,
  useSSL: SSL,
  accessKey: ACCESS_KEY,
  secretKey: SECRET_KEY,
});

const getObjectMap = () => {
  const map = {};

  return new Promise((resolve, reject) => {
    minioClient
      .listObjects(BUCKET_NAME, '', true)
      .on('data', obj => (map[obj.name] = obj))
      .on('error', err => reject(err))
      .on('end', () => resolve(map));
  });
};

const writeXCom = (data) => {
  return new Promise((resolve, reject) => {
    fs.writeFile(XCOM_FILE, JSON.stringify(data), (err) => {
        if (err) return reject(err);
        resolve();
    });
  });
}

const streamFileToMinio = (url) => {
  const protocol = new URL(url).protocol;
  const filename = path.basename(url);

  console.log(`uploading ${url}`);

  return new Promise((resolve, reject) => {
    fetch[protocol].get(url, httpOption, resp => {
      minioClient.putObject(BUCKET_NAME, filename, resp, (err, etag) => {
        if (err) return reject(err);
        else return resolve({bucketName: BUCKET_NAME, objectName: filename, etag});
      });
    });
  });
};

(async () => {
  try {
    const hasBucket = await minioClient.bucketExists(BUCKET_NAME);
    if (!hasBucket) await minioClient.makeBucket(BUCKET_NAME, REGION);

    const objectMap = await getObjectMap();
    console.log(`received ${FILE_URLS.length} urls to upload to MinIO.`)
    const skippedUrls = FILE_URLS.filter((url) => path.basename(url) in objectMap);
    for (const url of skippedUrls) {
      console.log(`skipping ${url}`);
    }
    const urlsToUpload = FILE_URLS.filter((url) => !(path.basename(url) in objectMap));
    // We use asyncForEach instead of Promise.all to avoid overloading the MinIO server
    // Ideally we'd have a queue system that limits the number of simultaneous uploads
    const uploadedObjects = await asyncMap(urlsToUpload, (url) => streamFileToMinio(url));
    await writeXCom({uploadedObjects, skippedUrls});
  } catch (err) {
    console.error(err);
  }
})();

async function asyncMap(array, callback) {
  const result = []
  for (let index = 0; index < array.length; index++) {
    result.push(await callback(array[index], index, array));
  }
  return result;
}
