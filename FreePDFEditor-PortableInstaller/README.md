# FreePDF Editor Pro — Windows 免 Python 安装包方案

这是 FreePDF Editor Pro 的 Windows 发布版工程。

## 最终用户

最终用户只需要运行：

`FreePDFEditorPro-Setup.exe`

无需安装 Python。

## 自动构建

推荐使用 GitHub Actions：

`.github/workflows/build-windows.yml`

构建完成后会输出：

- `FreePDFEditorPro-Setup.exe`
- `FreePDFEditorPro-Portable.zip`

详细说明见：

`BUILD-WITHOUT-PYTHON.md`
