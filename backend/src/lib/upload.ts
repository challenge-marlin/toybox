import multer from 'multer';
import path from 'path';
import fs from 'fs';

const uploadDirectory = path.join(process.cwd(), 'public', 'uploads');
// Ensure upload directory exists at startup
try {
  fs.mkdirSync(uploadDirectory, { recursive: true });
} catch {}

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, uploadDirectory),
  filename: (_req, file, cb) => {
    const unique = `${Date.now()}-${Math.round(Math.random() * 1e9)}`;
    cb(null, unique + path.extname(file.originalname || ''));
  }
});

// 許可MIME: jpg, jpeg, png, webp
const allowedImageMimeTypes = ['image/jpeg', 'image/png', 'image/webp'];
const allowedVideoMimeTypes = ['video/mp4', 'video/webm', 'video/ogg'];
const allowedZipMimeTypes = ['application/zip', 'application/x-zip-compressed', 'application/octet-stream'];

function makeFileFilter(type: UploadType) {
  return (_req: any, file: Express.Multer.File, cb: multer.FileFilterCallback) => {
    if (type === 'gamezip') {
      const isZip = allowedZipMimeTypes.includes(file.mimetype) || /\.zip$/i.test(file.originalname || '');
      if (isZip) return cb(null, true);
      return cb(new Error('Invalid file type. Only .zip is allowed for game uploads.'));
    }
    if (type === 'post') {
      const isImage = allowedImageMimeTypes.includes(file.mimetype);
      const isVideo = allowedVideoMimeTypes.includes(file.mimetype) || /\.(mp4|webm|ogg)$/i.test(file.originalname || '');
      if (isImage || isVideo) return cb(null, true);
      return cb(new Error('Invalid file type. Only jpg, jpeg, png, webp, mp4, webm, ogg are allowed.'));
    }
    if (allowedImageMimeTypes.includes(file.mimetype)) {
      return cb(null, true);
    }
    return cb(new Error('Invalid file type. Only jpg, jpeg, png, webp are allowed.'));
  };
}

type UploadType = 'avatar' | 'header' | 'post' | 'gamezip';

function getSizeLimit(type: UploadType): number {
  const envKey = `MAX_UPLOAD_MB_${type.toUpperCase()}`;
  const specific = process.env[envKey];
  if (specific) return parseInt(specific, 10) * 1024 * 1024;
  
  // Fallback to generic MAX_UPLOAD_MB, then default
  const generic = process.env.MAX_UPLOAD_MB;
  if (generic) return parseInt(generic, 10) * 1024 * 1024;
  
  // Default by type
  const defaults: Record<UploadType, number> = {
    avatar: 2,
    header: 5,
    post: 1024,
    gamezip: 1024
  };
  return defaults[type] * 1024 * 1024;
}

export function createUploadMiddleware(type: UploadType) {
  return multer({
    storage,
    limits: { fileSize: getSizeLimit(type) },
    fileFilter: makeFileFilter(type)
  });
}

// Default generic upload (fallback, 500MB for compatibility)
export const upload = multer({
  storage,
  limits: { fileSize: (parseInt(process.env.MAX_UPLOAD_MB || '500', 10)) * 1024 * 1024 },
  fileFilter: makeFileFilter('post')
});

// Typed uploads
export const uploadAvatar = createUploadMiddleware('avatar');
export const uploadHeader = createUploadMiddleware('header');
export const uploadPost = createUploadMiddleware('post');
export const uploadGameZip = createUploadMiddleware('gamezip');


