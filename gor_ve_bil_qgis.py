import os
import random
from qgis.core import (
    QgsProject,
    QgsDistanceArea,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsMarkerSymbol,
    QgsLineSymbol,
    QgsSingleSymbolRenderer,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling
)
from qgis.gui import QgsMapToolEmitPoint
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.utils import iface

# --- AYARLAR ---
FOTO_DIZINI = "C:/gor_ve_bil_for_ktu/fotolar"
HEDEF_KATMAN_ADI = "hedef_noktalar"

proje = QgsProject.instance()
katmanlar = proje.mapLayersByName(HEDEF_KATMAN_ADI)
if not katmanlar:
    raise Exception(f"'{HEDEF_KATMAN_ADI}' katmanı bulunamadı!")

hedef_katman = katmanlar[0]
noktalar = list(hedef_katman.getFeatures())
if not noktalar:
    raise Exception("Katmanda nokta bulunamadı! Lütfen hedef noktaları ekleyin.")

secilen = random.choice(noktalar)
hedef_id = secilen["id"]
hedef_geom = secilen.geometry().asPoint()

# --- ARAYÜZ (POP-UP) ---
class GorVeBilDialog(QDialog):
    def __init__(self, nokta_id):
        super().__init__(iface.mainWindow())
        self.setWindowTitle(f"Gör ve Bil - Nokta #{nokta_id}")
        self.resize(720, 520)
        self.nokta_id = nokta_id
        self.idx = 0
        self.yonler = [("k", "Kuzey"), ("d", "Doğu"), ("g", "Güney"), ("b", "Batı")]
        
        lay = QVBoxLayout(self)
        self.lbl_info = QLabel(f"<h2>Hedef Nokta #{nokta_id}</h2>Fotoğrafları inceleyip haritaya geçin.")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_info)
        
        self.lbl_img = QLabel()
        self.lbl_img.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_img)
        
        btn_lay = QHBoxLayout()
        self.btn_prev = QPushButton("◀ Önceki Yön")
        self.lbl_yon = QLabel()
        self.lbl_yon.setAlignment(Qt.AlignCenter)
        self.btn_next = QPushButton("Sonraki Yön ▶")
        btn_lay.addWidget(self.btn_prev)
        btn_lay.addWidget(self.lbl_yon)
        btn_lay.addWidget(self.btn_next)
        lay.addLayout(btn_lay)
        
        self.btn_go = QPushButton("Konumu Tahmin Et (Haritaya Tıkla)")
        self.btn_go.setStyleSheet("font-size: 14px; font-weight: bold; padding: 6px;")
        lay.addWidget(self.btn_go)
        
        self.btn_prev.clicked.connect(self.onceki)
        self.btn_next.clicked.connect(self.sonraki)
        self.btn_go.clicked.connect(self.accept)
        self.guncelle()

    def guncelle(self):
        kod, ad = self.yonler[self.idx]
        dosya = f"{kod}{self.nokta_id}.jpg"
        yol = os.path.join(FOTO_DIZINI, dosya)
        self.lbl_yon.setText(f"<b>{ad}</b> ({dosya})")
        if os.path.exists(yol):
            self.lbl_img.setPixmap(QPixmap(yol).scaled(660, 390, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_img.setText(f"Görsel bulunamadı:\n{yol}")

    def sonraki(self):
        self.idx = (self.idx + 1) % len(self.yonler)
        self.guncelle()

    def onceki(self):
        self.idx = (self.idx - 1) % len(self.yonler)
        self.guncelle()

# --- HARİTADA TIKLAMA VE JEODEZİK HESAPLAMA MOTORU ---
class OyunAraci:
    def __init__(self, hedef):
        self.canvas = iface.mapCanvas()
        self.crs_auth = self.canvas.mapSettings().destinationCrs().authid()
        self.hedef = hedef
        self.tahminler = []
        self.oyuncu = 1

        # Önceki turlardan kalan katmanları temizle
        for l_name in ["Tahmin_Noktalari", "GorVeBil_Sonuc"]:
            eski = proje.mapLayersByName(l_name)
            if eski:
                proje.removeMapLayer(eski[0].id())

        # 1. Tahminleri gösterecek nokta katmanı
        self.nokta_katmani = QgsVectorLayer(f"Point?crs={self.crs_auth}", "Tahmin_Noktalari", "memory")
        pr = self.nokta_katmani.dataProvider()
        pr.addAttributes([QgsField("Oyuncu", QVariant.String)])
        self.nokta_katmani.updateFields()

        sym = QgsMarkerSymbol.createSimple({'name': 'circle', 'size': '5', 'color': 'yellow', 'outline_color': 'black', 'outline_width': '1'})
        self.nokta_katmani.setRenderer(QgsSingleSymbolRenderer(sym))

        lbl = QgsPalLayerSettings()
        lbl.fieldName = "Oyuncu"
        lbl.enabled = True
        self.nokta_katmani.setLabeling(QgsVectorLayerSimpleLabeling(lbl))
        self.nokta_katmani.setLabelsEnabled(True)

        proje.addMapLayer(self.nokta_katmani)

        self.tool = QgsMapToolEmitPoint(self.canvas)
        self.tool.canvasClicked.connect(self.tiklandi)
        self.canvas.setMapTool(self.tool)
        iface.messageBar().pushInfo("Gör ve Bil", "1. Oyuncu: Harita üzerinde tahminini tıkla!")

    def tiklandi(self, pt):
        self.tahminler.append(pt)
        
        pr = self.nokta_katmani.dataProvider()
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(pt))
        feat.setAttributes([f"{self.oyuncu}. Oyuncu"])
        pr.addFeature(feat)
        self.nokta_katmani.updateExtents()
        self.nokta_katmani.triggerRepaint()

        if self.oyuncu == 1:
            self.oyuncu = 2
            iface.messageBar().pushInfo("Gör ve Bil", "1. Oyuncu işaretledi! Şimdi 2. Oyuncu tahminini tıklasın.")
        else:
            self.canvas.unsetMapTool(self.tool)
            self.bitir()

    def bitir(self):
        # Gerçek hedef noktayı göster
        pr = self.nokta_katmani.dataProvider()
        feat_hedef = QgsFeature()
        feat_hedef.setGeometry(QgsGeometry.fromPointXY(self.hedef))
        feat_hedef.setAttributes(["🎯 HEDEF"])
        pr.addFeature(feat_hedef)
        self.nokta_katmani.triggerRepaint()

        # Mesafe çizgileri katmanı
        cizgi_katmani = QgsVectorLayer(f"LineString?crs={self.crs_auth}", "GorVeBil_Sonuc", "memory")
        pr_cizgi = cizgi_katmani.dataProvider()
        pr_cizgi.addAttributes([QgsField("Oyuncu", QVariant.String), QgsField("Fark", QVariant.Double)])
        cizgi_katmani.updateFields()

        # --- JEODEZİK MESAFE HESAPLAYICI (GRS80 ELİPSOİDİ) ---
        da = QgsDistanceArea()
        da.setSourceCrs(self.canvas.mapSettings().destinationCrs(), proje.transformContext())
        da.setEllipsoid("GRS80")  # TUREF/ITRF için resmi jeodezik elipsoit

        skorlar = []
        metin = "🎯 Tur Bitti (Jeodezik Hesap)! 🎯\n\n"

        for i, p in enumerate(self.tahminler, 1):
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPolylineXY([p, self.hedef]))
            
            # Elipsoid üzerindeki jeodezik hat uzunluğu
            mesafe = round(da.measureLine(p, self.hedef), 2)
            
            feat.setAttributes([f"{i}. Oyuncu", mesafe])
            pr_cizgi.addFeature(feat)
            skorlar.append((i, mesafe))
            metin += f"{i}. Oyuncu: {mesafe} metre sapma\n"

        cizgi_katmani.updateExtents()

        sym_line = QgsLineSymbol.createSimple({'line_color': '#ff0000', 'line_width': '0.8', 'line_style': 'dash'})
        cizgi_katmani.setRenderer(QgsSingleSymbolRenderer(sym_line))

        lbl_line = QgsPalLayerSettings()
        lbl_line.fieldName = "concat(Oyuncu, ': ', to_string(round(Fark, 2)), ' m')"
        lbl_line.enabled = True
        cizgi_katmani.setLabeling(QgsVectorLayerSimpleLabeling(lbl_line))
        cizgi_katmani.setLabelsEnabled(True)

        proje.addMapLayer(cizgi_katmani)
        self.canvas.refresh()

        kazanan = min(skorlar, key=lambda x: x[1])
        metin += f"\n🏆 Kazanan: {kazanan[0]}. Oyuncu ({kazanan[1]} m farkla!)"
        QMessageBox.information(None, "Jeodezik Skorlar", metin)

# Başlat
win = GorVeBilDialog(hedef_id)
if win.exec_():
    global aktif_oyun
    aktif_oyun = OyunAraci(hedef_geom)


giriş ekranlı hali 
import os
import random
from qgis.core import (
    QgsProject,
    QgsDistanceArea,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsMarkerSymbol,
    QgsLineSymbol,
    QgsSingleSymbolRenderer,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling
)
from qgis.gui import QgsMapToolEmitPoint
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox, QStackedWidget, QWidget
)
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.utils import iface

# --- AYARLAR ---
FOTO_DIZINI = "C:/gor_ve_bil_for_ktu/fotolar"
HEDEF_KATMAN_ADI = "hedef_noktalar"

proje = QgsProject.instance()
katmanlar = proje.mapLayersByName(HEDEF_KATMAN_ADI)
if not katmanlar:
    raise Exception(f"'{HEDEF_KATMAN_ADI}' katmanı bulunamadı!")

hedef_katman = katmanlar[0]
noktalar = list(hedef_katman.getFeatures())
if not noktalar:
    raise Exception("Katmanda hedef nokta bulunamadı!")

secilen = random.choice(noktalar)
hedef_id = secilen["id"]
hedef_geom = secilen.geometry().asPoint()

# --- ÇOK SAYFALI OYUN PENCERESİ ---
class GorVeBilDialog(QDialog):
    def __init__(self, nokta_id):
        super().__init__(iface.mainWindow())
        self.setWindowTitle("Gör ve Bil - Kampüs Keşfi")
        self.resize(760, 580)
        self.nokta_id = nokta_id
        self.idx = 0
        self.yonler = [("k", "Kuzey"), ("d", "Doğu"), ("g", "Güney"), ("b", "Batı")]

        # Sayfa Yöneticisi
        self.stack = QStackedWidget(self)
        ana_duzen = QVBoxLayout(self)
        ana_duzen.addWidget(self.stack)

        # Sayfaları Oluştur
        self.giris_sayfasi = self.olustur_giris_sayfasi()
        self.foto_sayfasi = self.olustur_foto_sayfasi()

        self.stack.addWidget(self.giris_sayfasi)
        self.stack.addWidget(self.foto_sayfasi)

    def olustur_giris_sayfasi(self):
        sayfa = QWidget()
        lay = QVBoxLayout(sayfa)
        lay.setSpacing(15)

        baslik = QLabel("<h1>🌍 Gör ve Bil'e Hoş Geldiniz!</h1>")
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("color: #1a5276; margin-top: 10px;")
        lay.addWidget(baslik)

        kurallar = QLabel(
            "<div style='font-size: 13px; line-height: 1.6; background-color: #f8f9f9; padding: 15px; border-radius: 8px; border: 1px solid #d5dbdb;'>"
            "<b>Oyunun Amacı:</b><br>"
            "Rastgele belirlenen bir noktadan çekilmiş 4 yönlü (Kuzey, Doğu, Güney, Batı) arazi fotoğraflarını inceleyerek "
            "bu konumun harita üzerindeki yerini en az sapmayla tahmin etmektir.<br><br>"
            "<b>Nasıl Oynanır?</b><br>"
            "1. <b>'Oyuna Başla'</b> butonuna basarak fotoğrafları görüntüleyin.<br>"
            "2. Yön butonlarıyla çevredeki nirengileri, yolları ve binaları analiz edin.<br>"
            "3. <b>'Konumu Tahmin Et'</b> butonuna basıp harita tuvaline dönün.<br>"
            "4. Sırayla <b>1. Oyuncu</b> ve <b>2. Oyuncu</b> haritada tahmin ettikleri yeri sol tıklayarak işaretlesin.<br>"
            "5. GRS80 elipsoidi üzerinden jeodezik mesafe sapmaları hesaplanacak ve kazanan ilan edilecektir!"
            "</div>"
        )
        kurallar.setWordWrap(True)
        lay.addWidget(kurallar)

        btn_basla = QPushButton("Oyuna Başla ➔")
        btn_basla.setStyleSheet(
            "background-color: #27ae60; color: white; font-size: 15px; font-weight: bold; padding: 12px; border-radius: 6px;"
        )
        btn_basla.clicked.connect(lambda: self.stack.setCurrentWidget(self.foto_sayfasi))
        lay.addWidget(btn_basla)

        return sayfa

    def olustur_foto_sayfasi(self):
        sayfa = QWidget()
        lay = QVBoxLayout(sayfa)

        self.lbl_info = QLabel(f"<h3>Hedef Nokta #{self.nokta_id}</h3>4 yönü inceleyip haritaya geçin.")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_info)

        self.lbl_img = QLabel()
        self.lbl_img.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_img)

        btn_lay = QHBoxLayout()
        self.btn_prev = QPushButton("◀ Önceki Yön")
        self.lbl_yon = QLabel()
        self.lbl_yon.setAlignment(Qt.AlignCenter)
        self.btn_next = QPushButton("Sonraki Yön ▶")
        btn_lay.addWidget(self.btn_prev)
        btn_lay.addWidget(self.lbl_yon)
        btn_lay.addWidget(self.btn_next)
        lay.addLayout(btn_lay)

        self.btn_go = QPushButton("Konumu Tahmin Et (Haritaya Geç) 🎯")
        self.btn_go.setStyleSheet(
            "background-color: #2980b9; color: white; font-size: 14px; font-weight: bold; padding: 10px; border-radius: 6px;"
        )
        lay.addWidget(self.btn_go)

        self.btn_prev.clicked.connect(self.onceki)
        self.btn_next.clicked.connect(self.sonraki)
        self.btn_go.clicked.connect(self.accept)

        self.guncelle()
        return sayfa

    def guncelle(self):
        kod, ad = self.yonler[self.idx]
        dosya = f"{kod}{self.nokta_id}.jpg"
        yol = os.path.join(FOTO_DIZINI, dosya)
        self.lbl_yon.setText(f"<b>Bakış Yönü: {ad}</b> ({dosya})")
        if os.path.exists(yol):
            self.lbl_img.setPixmap(QPixmap(yol).scaled(660, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_img.setText(f"Görsel bulunamadı:\n{yol}")

    def sonraki(self):
        self.idx = (self.idx + 1) % len(self.yonler)
        self.guncelle()

    def onceki(self):
        self.idx = (self.idx - 1) % len(self.yonler)
        self.guncelle()

# --- HARİTADA TIKLAMA VE JEODEZİK MOTORU ---
class OyunAraci:
    def __init__(self, hedef):
        self.canvas = iface.mapCanvas()
        self.crs_auth = self.canvas.mapSettings().destinationCrs().authid()
        self.hedef = hedef
        self.tahminler = []
        self.oyuncu = 1

        for l_name in ["Tahmin_Noktalari", "GorVeBil_Sonuc"]:
            eski = proje.mapLayersByName(l_name)
            if eski:
                proje.removeMapLayer(eski[0].id())

        self.nokta_katmani = QgsVectorLayer(f"Point?crs={self.crs_auth}", "Tahmin_Noktalari", "memory")
        pr = self.nokta_katmani.dataProvider()
        pr.addAttributes([QgsField("Oyuncu", QVariant.String)])
        self.nokta_katmani.updateFields()

        sym = QgsMarkerSymbol.createSimple({'name': 'circle', 'size': '5', 'color': 'yellow', 'outline_color': 'black', 'outline_width': '1'})
        self.nokta_katmani.setRenderer(QgsSingleSymbolRenderer(sym))

        lbl = QgsPalLayerSettings()
        lbl.fieldName = "Oyuncu"
        lbl.enabled = True
        self.nokta_katmani.setLabeling(QgsVectorLayerSimpleLabeling(lbl))
        self.nokta_katmani.setLabelsEnabled(True)

        proje.addMapLayer(self.nokta_katmani)

        self.tool = QgsMapToolEmitPoint(self.canvas)
        self.tool.canvasClicked.connect(self.tiklandi)
        self.canvas.setMapTool(self.tool)
        iface.messageBar().pushInfo("Gör ve Bil", "1. Oyuncu: Harita üzerinde tahminini tıkla!")

    def tiklandi(self, pt):
        self.tahminler.append(pt)
        
        pr = self.nokta_katmani.dataProvider()
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(pt))
        feat.setAttributes([f"{self.oyuncu}. Oyuncu"])
        pr.addFeature(feat)
        self.nokta_katmani.updateExtents()
        self.nokta_katmani.triggerRepaint()

        if self.oyuncu == 1:
            self.oyuncu = 2
            iface.messageBar().pushInfo("Gör ve Bil", "1. Oyuncu işaretledi! Şimdi 2. Oyuncu tahminini tıklasın.")
        else:
            self.canvas.unsetMapTool(self.tool)
            self.bitir()

    def bitir(self):
        pr = self.nokta_katmani.dataProvider()
        feat_hedef = QgsFeature()
        feat_hedef.setGeometry(QgsGeometry.fromPointXY(self.hedef))
        feat_hedef.setAttributes(["🎯 HEDEF"])
        pr.addFeature(feat_hedef)
        self.nokta_katmani.triggerRepaint()

        cizgi_katmani = QgsVectorLayer(f"LineString?crs={self.crs_auth}", "GorVeBil_Sonuc", "memory")
        pr_cizgi = cizgi_katmani.dataProvider()
        pr_cizgi.addAttributes([QgsField("Oyuncu", QVariant.String), QgsField("Fark", QVariant.Double)])
        cizgi_katmani.updateFields()

        da = QgsDistanceArea()
        da.setSourceCrs(self.canvas.mapSettings().destinationCrs(), proje.transformContext())
        da.setEllipsoid("GRS80")

        skorlar = []
        metin = "🎯 Tur Bitti (Jeodezik Hesap)! 🎯\n\n"

        for i, p in enumerate(self.tahminler, 1):
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPolylineXY([p, self.hedef]))
            mesafe = round(da.measureLine(p, self.hedef), 2)
            feat.setAttributes([f"{i}. Oyuncu", mesafe])
            pr_cizgi.addFeature(feat)
            skorlar.append((i, mesafe))
            metin += f"{i}. Oyuncu: {mesafe} metre sapma\n"

        cizgi_katmani.updateExtents()

        sym_line = QgsLineSymbol.createSimple({'line_color': '#ff0000', 'line_width': '0.8', 'line_style': 'dash'})
        cizgi_katmani.setRenderer(QgsSingleSymbolRenderer(sym_line))

        lbl_line = QgsPalLayerSettings()
        lbl_line.fieldName = "concat(Oyuncu, ': ', to_string(round(Fark, 2)), ' m')"
        lbl_line.enabled = True
        cizgi_katmani.setLabeling(QgsVectorLayerSimpleLabeling(lbl_line))
        cizgi_katmani.setLabelsEnabled(True)

        proje.addMapLayer(cizgi_katmani)
        self.canvas.refresh()

        kazanan = min(skorlar, key=lambda x: x[1])
        metin += f"\n🏆 Kazanan: {kazanan[0]}. Oyuncu ({kazanan[1]} m farkla!)"
        QMessageBox.information(None, "Sonuçlar", metin)

# Başlat
win = GorVeBilDialog(hedef_id)
if win.exec_():
    global aktif_oyun
    aktif_oyun = OyunAraci(hedef_geom)
