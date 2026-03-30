import { createReadStream, existsSync } from 'node:fs';
import { stat } from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';

const DIST_DIR = path.join(process.cwd(), 'dist');
const INDEX_PATH = path.join(DIST_DIR, 'index.html');
const HOST = '0.0.0.0';
const PORT = Number(process.env.PORT || 4173);

const MIME_TYPES = {
  '.css': 'text/css; charset=utf-8',
  '.gif': 'image/gif',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.webp': 'image/webp',
};

function sendFile(response, filePath) {
  const extension = path.extname(filePath).toLowerCase();
  response.writeHead(200, {
    'Content-Type': MIME_TYPES[extension] || 'application/octet-stream',
    'Cache-Control': filePath === INDEX_PATH ? 'no-cache' : 'public, max-age=31536000, immutable',
  });
  createReadStream(filePath).pipe(response);
}

function isAssetRequest(requestPath) {
  return path.extname(requestPath) !== '';
}

async function resolveFilePath(requestPath) {
  const normalizedPath = path.normalize(decodeURIComponent(requestPath)).replace(/^(\.\.[\\/])+/, '');
  const safePath = normalizedPath === path.sep ? '' : normalizedPath;
  const candidatePath = path.join(DIST_DIR, safePath);

  if (existsSync(candidatePath)) {
    const fileStat = await stat(candidatePath);
    if (fileStat.isFile()) {
      return candidatePath;
    }
    const nestedIndex = path.join(candidatePath, 'index.html');
    if (existsSync(nestedIndex)) {
      return nestedIndex;
    }
  }

  if (isAssetRequest(requestPath)) {
    return null;
  }

  return INDEX_PATH;
}

const server = http.createServer(async (request, response) => {
  try {
    const url = new URL(request.url || '/', `http://${request.headers.host || 'localhost'}`);
    const filePath = await resolveFilePath(url.pathname);

    if (!filePath) {
      response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      response.end('Not found');
      return;
    }

    sendFile(response, filePath);
  } catch (error) {
    console.error('Failed to serve frontend request', error);
    response.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
    response.end('Internal server error');
  }
});

server.listen(PORT, HOST, () => {
  console.log(`Frontend listening on http://${HOST}:${PORT}`);
});
