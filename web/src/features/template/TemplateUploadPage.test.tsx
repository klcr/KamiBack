import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { TemplateUploadPage } from './TemplateUploadPage';

describe('TemplateUploadPage', () => {
  it('renders file input', () => {
    render(<TemplateUploadPage onParsed={vi.fn()} />);
    const input = screen.getByLabelText(/HTML テンプレートファイル/);
    expect(input).toBeDefined();
    expect(input.getAttribute('accept')).toBe('.html');
  });

  it('renders heading', () => {
    render(<TemplateUploadPage onParsed={vi.fn()} />);
    expect(screen.getByText('テンプレートアップロード')).toBeDefined();
  });
});
