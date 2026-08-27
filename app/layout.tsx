import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '埋點分析建立工具',
  description: '從 Figma 頁面盤點產品事件，整理第一階段埋點計畫並匯出 Excel 表格。',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-Hant">
      <body>{children}</body>
    </html>
  );
}
