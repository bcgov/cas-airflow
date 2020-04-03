const Minio = require('minio');
const argv = require('yargs').argv;

const END_POINT = argv.host || process.env.MINIO_HOST;
const PORT = argv.port || (process.env.MINIO_PORT && parseInt(process.env.MINIO_PORT, 10));
const SSL = argv.ssl || process.env.MINIO_SSL === 'true';
const ACCESS_KEY = argv.access_key || process.env.MINIO_ACCESS_KEY;
const SECRET_KEY = argv.secret_key || process.env.MINIO_SECRET_KEY;
const BUCKET_NAME = argv.bucket;

const minioClient = new Minio.Client({
  endPoint: END_POINT,
  port: PORT,
  useSSL: SSL,
  accessKey: ACCESS_KEY,
  secretKey: SECRET_KEY,
});

const getObjectList = () => {
  const list = [];

  return new Promise((resolve, reject) => {
    minioClient
      .listObjects(BUCKET_NAME, '', true)
      .on('data', obj => list.push(obj.name))
      .on('error', err => reject(err))
      .on('end', () => resolve(list));
  });
};

(async () => {
  try {
    const hasBucket = await minioClient.bucketExists(BUCKET_NAME);
    if (!hasBucket) return;

    const objectList = await getObjectList();
    await minioClient.removeObjects(BUCKET_NAME, objectList);
    await minioClient.removeBucket(BUCKET_NAME);
  } catch (err) {
    console.error(err);
  }
})();
