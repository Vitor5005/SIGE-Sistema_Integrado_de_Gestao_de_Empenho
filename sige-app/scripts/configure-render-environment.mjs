import { writeFileSync } from 'node:fs';

const configuredApiUrl = process.env.API_URL?.replace(/\/$/, '');

if (!configuredApiUrl) {
  throw new Error('A variavel API_URL nao foi definida pelo Render.');
}

const apiUrl = configuredApiUrl.startsWith('/')
  ? configuredApiUrl
  : new URL('/api/v1', `${configuredApiUrl}/`).toString().replace(/\/$/, '');
const environment = `export const environment = ${JSON.stringify({ API_URL: apiUrl }, null, 2)};\n`;

writeFileSync('src/app/environments/environment.ts', environment, 'utf8');
console.log(`API de producao configurada em ${apiUrl}`);
