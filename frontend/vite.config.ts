import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import {resolve} from 'path'
import { federation } from '@module-federation/vite'

// Custom plugin to inject remote stylesheet
const injectRemoteStylesheet = () => ({
  name: 'inject-remote-stylesheet',
  transformIndexHtml(html: string) {
    return html.replace(
      '</head>',
      `<link rel="stylesheet" href="https://auth-layout.vercel.app/_next/static/chunks/pages/_app.css" media="all" importance="high" />\n</head>`
    )
  }
})

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(),
    injectRemoteStylesheet(),
    federation({
      name: 'cluster',
      filename: 'assets/remoteEntry.js',
      remotes: {
        auth: 'auth@https://auth-layout.vercel.app/_next/static/chunks/remoteEntry.js',
      },
      shared: ['react', 'react-dom', 'react-router-dom','@clerk/clerk-react'],
    })
  ],
  build: {
    target: 'esnext', 
    outDir: '../home/static',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: resolve(__dirname, 'index.html'),
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]'
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  }
})
