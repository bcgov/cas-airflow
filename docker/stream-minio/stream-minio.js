const path = require('path');
const Minio = require('minio');
const argv = require('yargs').argv;

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

const streamFileToMinio = (url, objectMap = {}) => {
  const protocol = new URL(url).protocol;
  const filename = path.basename(url);

  if (objectMap[filename]) {
    console.log(`skipping ${url}`);
    return;
  }

  console.log(`uploading ${url}`);

  return new Promise((resolve, reject) => {
    fetch[protocol].get(url, httpOption, resp => {
      minioClient.putObject(BUCKET_NAME, filename, resp, (err, etag) => {
        if (err) return reject(err);
        else return resolve(etag);
      });
    });
  });
};

(async () => {
  try {
    const hasBucket = await minioClient.bucketExists(BUCKET_NAME);
    if (!hasBucket) await minioClient.makeBucket(BUCKET_NAME, REGION);

    const objectMap = await getObjectMap();
    await asyncForEach(FILE_URLS, url => streamFileToMinio(url, objectMap));
  } catch (err) {
    console.error(err);
  }
})();

async function asyncForEach(array, callback) {
  for (let index = 0; index < array.length; index++) {
    await callback(array[index], index, array);
  }
}
