import react from '@vitejs/plugin-react-swc';
import { defineConfig } from 'vite';
// import mkcert from 'vite-plugin-mkcert';
import { viteStaticCopy } from 'vite-plugin-static-copy';

// https://vite.dev/config/
export default defineConfig({
	plugins: [
		// mkcert(),
		react(),
		viteStaticCopy({
			targets: [
				{
					src: 'node_modules/pyodide/*.*',
					dest: './pyodide',
				},
			],
		}),
	],
	assetsInclude: ['**/*.md'],
	resolve: {
		alias: {
			'node-fetch': 'isomorphic-fetch',
		},
	},
});
