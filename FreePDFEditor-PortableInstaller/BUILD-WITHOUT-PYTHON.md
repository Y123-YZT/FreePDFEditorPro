# 不安装 Python 也能获得 EXE / 安装包

这个方案的核心是：

- **最终用户完全不需要 Python**
- **最终用户不需要安装 PySide6 / PyMuPDF**
- Windows 安装包内包含程序运行所需的 Python 运行时和依赖
- 构建工作由 GitHub Actions 在 Windows 云端完成
- 最终得到：
  - `FreePDFEditorPro-Setup.exe`：标准 Windows 安装程序
  - `FreePDFEditorPro-Portable.zip`：免安装便携版

## 推荐方法：GitHub Actions 自动构建

1. 在 GitHub 新建一个仓库。
2. 把整个项目上传到仓库。
3. 打开仓库的 `Actions`。
4. 选择 `Build Windows EXE and Installer`。
5. 点击 `Run workflow`。
6. 构建完成后打开该次运行的 `Artifacts`。
7. 下载 `FreePDFEditorPro-Windows`。
8. 解压后即可得到：
   - `FreePDFEditorPro-Setup.exe`
   - `FreePDFEditorPro-Portable.zip`

### 用户电脑需要什么？

安装包安装后的用户电脑：

- 不需要 Python
- 不需要 pip
- 不需要 PySide6
- 不需要 PyMuPDF
- 不需要开发环境

双击安装程序即可。

## 如果你自己以后想在本机构建

本机开发者仍需要 Python 作为“构建工具”，但这只是开发/打包电脑需要，不是最终用户需要。

## 注意

这是“免 Python 运行”的 Windows 桌面程序，而不是把 Python 从源代码中消灭。PyInstaller 会把 Python 运行时和依赖打进应用目录，因此最终用户无需单独安装 Python。
