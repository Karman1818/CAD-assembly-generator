import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'CAD Assembly Generator',
  description: 'Z-up 3D renderer and CadQuery converter',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pl">
      <body className="font-sans antialiased text-slate-200 selection:bg-indigo-500/30">
        {children}
      </body>
    </html>
  )
}
