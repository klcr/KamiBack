/**
 * ページ識別コード（QR placeholder）コンポーネント。
 *
 * QRコードライブラリの導入前は、content テキストを表示するプレースホルダー。
 * 印刷時にQRとして機能するには qrcode ライブラリの統合が必要。
 */

import type { PageIdentifier } from '../../lib/types/manifest';

interface Props {
  readonly identifier: PageIdentifier;
}

export function PageIdCode({ identifier }: Props) {
  return (
    <div
      className="page-id-code"
      style={{
        position: 'absolute',
        left: `${identifier.position.x}mm`,
        top: `${identifier.position.y}mm`,
        width: `${identifier.sizeMm}mm`,
        height: `${identifier.sizeMm}mm`,
        border: '0.3mm solid black',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '1.5mm',
        fontFamily: 'monospace',
        overflow: 'hidden',
      }}
      data-content={identifier.content}
    >
      {identifier.content}
    </div>
  );
}
