/**
 * Blob URLで新規ウィンドウを開いて印刷する。
 *
 * ボタンの onClick ハンドラ内で同期的に呼ばれることを前提とする
 * （非同期だとポップアップブロッカーに阻まれる可能性がある）。
 */

export function openPrintWindow(html: string): void {
  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const win = window.open(url, '_blank');
  if (win) {
    win.addEventListener('load', () => {
      win.print();
    });
    win.addEventListener('afterprint', () => {
      win.close();
      URL.revokeObjectURL(url);
    });
  } else {
    URL.revokeObjectURL(url);
  }
}
