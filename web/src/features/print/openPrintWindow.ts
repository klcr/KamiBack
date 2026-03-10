/**
 * 新規ウィンドウを開いてHTMLを書き込み、印刷する。
 *
 * blob URL 方式では load イベントがナビゲーションで失われるため、
 * document.write で直接 HTML を書き込む方式を採用する。
 * ボタンの onClick ハンドラ内で同期的に呼ばれることを前提とする
 * （非同期だとポップアップブロッカーに阻まれる可能性がある）。
 */

export function openPrintWindow(html: string): void {
  const win = window.open('', '_blank');
  if (!win) return;

  win.document.open();
  win.document.write(html);
  win.document.close();

  win.addEventListener('afterprint', () => {
    win.close();
  });

  // コンテンツ描画完了後に印刷ダイアログを表示
  win.addEventListener('load', () => {
    win.print();
  });
}
