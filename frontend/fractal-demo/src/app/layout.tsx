import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Arxos Fractal Demo - Infinite Zoom Architecture',
  description: 'Interactive demonstration of fractal ArxObject system with Google Maps-style lazy loading',
  keywords: 'arxos, fractal, infinite zoom, architecture, BIM, lazy loading',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
        <Toaster 
          position="top-right"
          toastOptions={{
            style: {
              background: '#333',
              color: '#fff',
              border: '1px solid #555',
            },
          }}
        />
      </body>
    </html>
  )
}