import { Outfit } from 'next/font/google'
import type { Metadata } from 'next'
import './globals.css'

const outfit = Outfit({ subsets: ['latin'], variable: '--font-outfit' })

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
    <html lang="pl" className={outfit.variable}>
      <body className="font-sans antialiased text-slate-200 selection:bg-indigo-500/30">
        {children}
      </body>
    </html>
  )
}
