import sys
from pathlib import Path
from copy import deepcopy

import fitz
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QListWidget,
    QListWidgetItem, QSplitter, QInputDialog, QFrame, QToolButton,
    QStackedWidget, QStyle
)


class Canvas(QWidget):
    def __init__(self, window):
        super().__init__()
        self.w = window
        self.drag_start = None
        self.drag_last = None
        self.drawing = False
        self.setMinimumSize(600, 650)
        self.setMouseTracking(True)

    def mousePressEvent(self, e):
        if not self.w.doc:
            return
        self.drag_start = e.position()
        self.drag_last = e.position()
        if self.w.tool == "text":
            self.w.add_text(e.position())
        elif self.w.tool in ("draw", "highlight"):
            self.drawing = True

    def mouseMoveEvent(self, e):
        if self.drawing:
            self.drag_last = e.position()
            self.update()

    def mouseReleaseEvent(self, e):
        if not self.drawing:
            return
        self.drag_last = e.position()
        if self.w.tool == "draw":
            self.w.add_line(self.drag_start, self.drag_last)
        elif self.w.tool == "highlight":
            self.w.add_highlight(self.drag_start, self.drag_last)
        self.drawing = False
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#525659"))
        if self.w.pixmap:
            x = (self.width()-self.w.pixmap.width())//2
            y = max(18, (self.height()-self.w.pixmap.height())//2)
            p.drawPixmap(x, y, self.w.pixmap)
            if self.drawing and self.drag_start and self.drag_last:
                if self.w.tool == "draw":
                    p.setPen(QPen(QColor("#d92d20"), 3))
                    p.drawLine(self.drag_start, self.drag_last)
                else:
                    p.setPen(QPen(QColor("#e0a800"), 2))
                    p.setBrush(QColor(255, 220, 0, 70))
                    p.drawRect(QRectF(self.drag_start, self.drag_last))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FreePDF Editor Pro")
        self.resize(1400, 900)
        self.doc = None
        self.path = None
        self.page_index = 0
        self.zoom = 1.15
        self.pixmap = None
        self.tool = "select"
        self.history = []
        self.dark = False
        self.build()

    def build(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        self.make_topbar(layout)
        self.make_tabs(layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        left = self.make_sidebar()
        splitter.addWidget(left)

        center = QWidget()
        cv = QVBoxLayout(center)
        cv.setContentsMargins(0,0,0,0)
        self.canvas = Canvas(self)
        cv.addWidget(self.canvas)
        self.make_bottombar(cv)
        splitter.addWidget(center)
        splitter.setStretchFactor(1,1)

        right = self.make_rightbar()
        splitter.addWidget(right)
        splitter.setSizes([210, 950, 180])
        layout.addWidget(splitter, 1)

        self.apply_theme()

    def make_topbar(self, parent):
        bar = QFrame()
        bar.setObjectName("top")
        row = QHBoxLayout(bar)
        row.setContentsMargins(14,8,14,8)

        logo = QLabel("◈  FreePDF")
        logo.setObjectName("logo")
        row.addWidget(logo)
        row.addSpacing(20)

        for text, fn in [
            ("打开", self.open_pdf),
            ("保存", self.save),
            ("另存为", self.save_as),
            ("撤销", self.undo),
            ("重做", self.redo),
        ]:
            b = QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)

        row.addStretch()
        self.search = QPushButton("🔎  查找")
        self.search.clicked.connect(self.find_text)
        row.addWidget(self.search)
        theme = QPushButton("☾")
        theme.setToolTip("切换深色/浅色")
        theme.clicked.connect(self.toggle_theme)
        row.addWidget(theme)
        parent.addWidget(bar)

    def make_tabs(self, parent):
        bar = QFrame()
        row = QHBoxLayout(bar)
        row.setContentsMargins(14,4,14,4)
        for text, fn in [
            ("主页", lambda: self.set_tool("select")),
            ("编辑", lambda: self.set_tool("text")),
            ("注释", lambda: self.set_tool("highlight")),
            ("绘图", lambda: self.set_tool("draw")),
            ("页面", self.organize_pages),
        ]:
            b = QPushButton(text)
            b.setProperty("tab", True)
            b.clicked.connect(fn)
            row.addWidget(b)
        row.addStretch()
        parent.addWidget(bar)

    def make_sidebar(self):
        panel = QFrame()
        panel.setObjectName("side")
        v = QVBoxLayout(panel)
        title = QLabel("页面")
        title.setObjectName("section")
        v.addWidget(title)
        self.pages = QListWidget()
        self.pages.setDragDropMode(QListWidget.InternalMove)
        self.pages.model().rowsMoved.connect(self.pages_reordered)
        self.pages.currentRowChanged.connect(self.goto)
        v.addWidget(self.pages, 1)
        for txt, fn in [("+ 插入页面", self.insert_pdf), ("🗑 删除页面", self.delete_page)]:
            b=QPushButton(txt); b.clicked.connect(fn); v.addWidget(b)
        return panel

    def make_rightbar(self):
        panel=QFrame(); panel.setObjectName("tools")
        v=QVBoxLayout(panel)
        title=QLabel("快速工具"); title.setObjectName("section"); v.addWidget(title)
        tools=[
            ("↖ 选择", "select"),
            ("T  添加文字", "text"),
            ("▣  高亮", "highlight"),
            ("╱  画笔", "draw"),
        ]
        for text, tool in tools:
            b=QPushButton(text); b.clicked.connect(lambda _,t=tool:self.set_tool(t)); v.addWidget(b)
        v.addStretch()
        merge=QPushButton("合并 PDF"); merge.clicked.connect(self.merge); v.addWidget(merge)
        return panel

    def make_bottombar(self, parent):
        bar=QFrame(); row=QHBoxLayout(bar)
        self.info=QLabel("未打开文件")
        self.page_label=QLabel("0 / 0")
        prev=QPushButton("‹"); prev.clicked.connect(self.prev)
        nxt=QPushButton("›"); nxt.clicked.connect(self.next)
        row.addWidget(self.info); row.addStretch(); row.addWidget(prev); row.addWidget(self.page_label); row.addWidget(nxt)
        row.addSpacing(20)
        row.addWidget(QLabel("−"))
        s=QSlider(Qt.Horizontal); s.setRange(50,250); s.setValue(115); s.valueChanged.connect(self.set_zoom); s.setMaximumWidth(160)
        row.addWidget(s); row.addWidget(QLabel("+"))
        parent.addWidget(bar)

    def apply_theme(self):
        if self.dark:
            self.setStyleSheet("""
            QWidget{background:#202124;color:#e8eaed}
            QFrame#top{background:#292a2d;border-bottom:1px solid #444}
            QFrame#side,QFrame#tools{background:#252629}
            QLabel#logo{font-size:20px;font-weight:700}
            QLabel#section{font-size:16px;font-weight:700;padding:8px}
            QPushButton{background:#303134;border:1px solid #4a4b4f;border-radius:6px;padding:7px 12px}
            QPushButton:hover{background:#3c4043}
            QListWidget{background:#1f2023;border:0}
            QListWidget::item{padding:9px;border-radius:5px}
            QListWidget::item:selected{background:#3f51b5}
            """)
        else:
            self.setStyleSheet("""
            QWidget{background:#f5f6f8;color:#202124}
            QFrame#top{background:#ffffff;border-bottom:1px solid #dadce0}
            QFrame#side,QFrame#tools{background:#ffffff}
            QLabel#logo{font-size:20px;font-weight:700}
            QLabel#section{font-size:16px;font-weight:700;padding:8px}
            QPushButton{background:#ffffff;border:1px solid #dadce0;border-radius:6px;padding:7px 12px}
            QPushButton:hover{background:#eef3ff}
            QListWidget{background:#f8f9fa;border:0}
            QListWidget::item{padding:9px;border-radius:5px}
            QListWidget::item:selected{background:#dbe7ff;color:#174ea6}
            """)

    def toggle_theme(self):
        self.dark=not self.dark
        self.apply_theme()

    def set_tool(self, t):
        self.tool=t
        names={"select":"选择","text":"添加文字","highlight":"高亮","draw":"画笔"}
        self.statusBar().showMessage("工具："+names.get(t,t))

    def open_pdf(self):
        path,_=QFileDialog.getOpenFileName(self,"打开 PDF","","PDF (*.pdf)")
        if not path:return
        try:
            if self.doc:self.doc.close()
            self.doc=fitz.open(path); self.path=path; self.page_index=0; self.history=[]
            self.populate(); self.render()
            self.info.setText(Path(path).name)
        except Exception as e: QMessageBox.critical(self,"打开失败",str(e))

    def populate(self):
        self.pages.blockSignals(True); self.pages.clear()
        for i in range(len(self.doc)):
            it=QListWidgetItem(f"第 {i+1} 页")
            self.pages.addItem(it)
        self.pages.setCurrentRow(self.page_index); self.pages.blockSignals(False)

    def render(self):
        if not self.doc:return
        pix=self.doc[self.page_index].get_pixmap(matrix=fitz.Matrix(self.zoom,self.zoom),alpha=False)
        img=QImage(pix.samples,pix.width,pix.height,pix.stride,QImage.Format_RGB888)
        self.pixmap=QPixmap.fromImage(img.copy())
        self.canvas.update()
        self.page_label.setText(f"{self.page_index+1} / {len(self.doc)}")

    def goto(self,row):
        if self.doc and row>=0:self.page_index=row; self.render()

    def prev(self):
        if self.doc and self.page_index>0:self.pages.setCurrentRow(self.page_index-1)
    def next(self):
        if self.doc and self.page_index<len(self.doc)-1:self.pages.setCurrentRow(self.page_index+1)

    def set_zoom(self,v):
        self.zoom=v/100; self.render()

    def pdfpoint(self,p):
        x=(self.canvas.width()-self.pixmap.width())/2
        y=max(18,(self.canvas.height()-self.pixmap.height())/2)
        return fitz.Point((p.x()-x)/self.zoom,(p.y()-y)/self.zoom)

    def snapshot(self):
        if self.doc:
            self.history.append(self.doc.tobytes(garbage=4,deflate=True))
            if len(self.history)>10:self.history.pop(0)

    def add_text(self,pos):
        text,ok=QInputDialog.getText(self,"添加文字","请输入文字：")
        if ok and text:
            self.snapshot()
            self.doc[self.page_index].insert_text(self.pdfpoint(pos),text,fontsize=16,color=(0,0,0))
            self.render()

    def add_line(self,a,b):
        self.snapshot(); self.doc[self.page_index].draw_line(self.pdfpoint(a),self.pdfpoint(b),color=(0.85,0.1,0.1),width=2); self.render()

    def add_highlight(self,a,b):
        self.snapshot()
        r=fitz.Rect(self.pdfpoint(a),self.pdfpoint(b))
        self.doc[self.page_index].add_highlight_annot(r).update()
        self.render()

    def delete_page(self):
        if not self.doc or len(self.doc)<=1:return
        self.snapshot(); self.doc.delete_page(self.page_index)
        self.page_index=min(self.page_index,len(self.doc)-1); self.populate(); self.render()

    def insert_pdf(self):
        if not self.doc:return
        p,_=QFileDialog.getOpenFileName(self,"插入 PDF","","PDF (*.pdf)")
        if not p:return
        self.snapshot(); d=fitz.open(p); self.doc.insert_pdf(d,start_at=self.page_index+1); d.close()
        self.populate(); self.render()

    def pages_reordered(self,*args):
        # QListWidget visual order; apply order to PDF.
        if not self.doc or self.pages.count()!=len(self.doc): return
        order=[self.pages.row(self.pages.item(i)) for i in range(self.pages.count())]
        # Reconstruct from current PDF by saving each page as a temporary document.
        src=self.doc
        new=fitz.open()
        for old_index in order:
            new.insert_pdf(src,from_page=old_index,to_page=old_index)
        self.snapshot(); self.doc.close(); self.doc=new
        self.page_index=min(self.page_index,len(self.doc)-1)
        self.render()

    def organize_pages(self):
        self.statusBar().showMessage("页面管理：可在左侧拖拽页面排序")

    def merge(self):
        paths,_=QFileDialog.getOpenFileNames(self,"选择 PDF","","PDF (*.pdf)")
        if len(paths)<2:return
        out,_=QFileDialog.getSaveFileName(self,"保存合并 PDF","merged.pdf","PDF (*.pdf)")
        if not out:return
        result=fitz.open()
        try:
            for p in paths:
                d=fitz.open(p); result.insert_pdf(d); d.close()
            result.save(out); result.close()
            QMessageBox.information(self,"完成","合并成功")
        except Exception as e:
            result.close(); QMessageBox.critical(self,"失败",str(e))

    def save(self):
        if not self.doc:return
        if not self.path:return self.save_as()
        self._save(self.path)

    def save_as(self):
        if not self.doc:return
        out,_=QFileDialog.getSaveFileName(self,"另存为","document.pdf","PDF (*.pdf)")
        if out:self._save(out)

    def _save(self,out):
        try:
            self.doc.save(out,garbage=4,deflate=True)
            self.path=out; self.info.setText(Path(out).name)
            self.statusBar().showMessage("已保存")
        except Exception as e:QMessageBox.critical(self,"保存失败",str(e))

    def undo(self):
        if not self.history or not self.doc:return
        data=self.history.pop()
        current=self.doc.tobytes(garbage=4,deflate=True)
        self.doc.close()
        self.doc=fitz.open(stream=data,filetype="pdf")
        self.populate(); self.render()
        self.statusBar().showMessage("已撤销")

    def redo(self):
        self.statusBar().showMessage("重做历史将在后续版本加入")

    def find_text(self):
        if not self.doc:return
        text,ok=QInputDialog.getText(self,"查找","输入要查找的文字：")
        if not ok or not text:return
        for i in range(len(self.doc)):
            if self.doc[i].search_for(text):
                self.page_index=i; self.pages.setCurrentRow(i)
                self.statusBar().showMessage(f"找到：第 {i+1} 页")
                return
        QMessageBox.information(self,"查找","没有找到该文字。")


def main():
    app=QApplication(sys.argv)
    app.setApplicationName("FreePDF Editor Pro")
    app.setFont(QFont("Microsoft YaHei UI",10))
    w=MainWindow(); w.show()
    sys.exit(app.exec())


if __name__=="__main__":
    main()
