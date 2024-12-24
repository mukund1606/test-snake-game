import archiver from 'archiver';
import fs from 'fs';
import { Hono } from 'hono';
import { cors } from 'hono/cors';

const app = new Hono();
app.use(cors());

app.get('/', (c) => {
	return c.text('Hello Hono!');
});

const games = ['snake_game'];

app.post('/assets', async (c) => {
	const data = await c.req.json();
	const gameName = data.gameName;
	if (games.includes(gameName)) {
		const time = new Date().toISOString().replace(/:/g, '-');
		const zipName = `zips/${gameName}_${time}.zip`;

		// Create a writable stream for the zip file
		const output = fs.createWriteStream(zipName);
		const archive = archiver('zip', {
			zlib: { level: 9 }, // Compression level
		});

		// Pipe the archive data to the file
		archive.pipe(output);

		// Set the base directory for the glob pattern
		archive.glob('**/*', {
			cwd: gameName, // Set the base directory to the game folder
			ignore: ['main.py'], // Exclude the main.py file
			dot: true, // Include hidden files if needed
		});

		// Finalize the archive
		await archive.finalize();

		// Wait for the zip file to finish writing
		await new Promise((resolve, reject) => {
			output.on('close', resolve);
			output.on('error', reject);
		});

		const fileData = fs.readFileSync(zipName);
		fs.unlinkSync(zipName);
		return new Response(fileData, {
			headers: {
				'Content-Type': 'application/zip',
				'Content-Disposition': `attachment; filename="${gameName}.zip"`,
			},
		});
	}
	return new Response(null, { status: 404 });
});

app.post('/code', async (c) => {
	const data = await c.req.json();
	const gameName = data.gameName;
	if (games.includes(gameName)) {
		const fileData = fs.readFileSync(gameName + '/main.py');
		return new Response(fileData, {
			headers: {
				'Content-Type': 'text/plain',
				'Content-Disposition': `attachment; filename="main.py"`,
			},
		});
	}
	return new Response(null, { status: 404 });
});

export default app;
