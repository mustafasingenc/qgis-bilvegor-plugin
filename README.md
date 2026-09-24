# Gör ve Bil - Kampüs Keşfi (QGIS Mekânsal Oyun Aracı)

**Gör ve Bil**, QGIS masaüstü ortamında kullanıcıların mekânsal algısını ve nirengi okuma becerilerini test etmek amacıyla geliştirilmiş etkileşimli bir coğrafi tahmin oyunudur. 

Kullanıcılar rastgele gelen hedef noktaya ait 4 yönlü (Kuzey, Doğu, Güney, Batı) arazi fotoğraflarını inceleyerek harita tuvali üzerinde konum tahmini yapar; sistem ise GRS80 elipsoidi üzerinden jeodezik sapmaları hesaplayarak kazananı belirler.

---

## 💡 Geliştirme Süreci & Proje Notu (Yapay Zeka Destekli Geliştirme)
Bu proje, **geleneksel yazılım/kodlama geçmişine sahip olunmadan, modern üretken yapay zeka araçları bir "yardımcı mühendis" (co-pilot) olarak kullanılarak** hayata geçirilmiştir.

* **Fikir & Kurgu:** Oyunun senaryosu, haritacılık/CBS mantığı, çok oyunculu yarışma mekaniği ve jeodezik hesap gereksinimi tarafımdan kurgulanmıştır.
* **Veri & Dosya Mimarisi:** Projenin arka planda kusursuz çalışabilmesi için gereken dosya/klasör hiyerarşisi, hedef nokta öznitelik tabloları, fotoğraf isimlendirme standartları ve QGIS proje ortamı tarafımdan hazırlanıp sisteme entegre edilmiştir.
* **Kodlama & Dokümantasyon:** Python/PyQGIS ve PyQt arayüz kodlarının tamamı, belirlenen iş akışına göre **üretken yapay zeka modelleri yönlendirilerek yazdırılmış ve test edilmiştir.** Aşağıda listelenen teknik detaylar ve mimari açıklamalar da yapay zeka tarafından belgelendirilmiştir.

---

## 📁 Gerekli Dosya ve Veri Yapısı (Yerel Kurulum)
Betik yerel bir makinede çalıştırılmadan önce şu veri ve dizin yapısının hazır olması gerekmektedir:

1. **Fotoğraf Dizini:**  
   Fotoğraflar varsayılan olarak şu klasör yolunda aranır:
   `C:/gor_ve_bil_for_ktu/fotolar/`
   
   *İsimlendirme Standardı:*  
   Her hedef nokta için yön harfi + nokta id'si kullanılmalıdır (`k1.jpg`, `d1.jpg`, `g1.jpg`, `b1.jpg`).  
   - `k`: Kuzey  
   - `d`: Doğu  
   - `g`: Güney  
   - `b`: Batı

2. **QGIS Katman Gereksinimi:**  
   Açık olan QGIS projesinde adı birebir `hedef_noktalar` olan bir nokta vektör katmanı ve bu katmanda tamsayı formatında `id` öznitelik sütunu bulunmalıdır.

---

## 🛠 Teknik Detaylar (Yapay Zeka Tarafından Üretilen Altyapı)
Aşağıdaki teknik mimari ve kod blokları, yapay zeka yönlendirmeleriyle oluşturulmuştur:

- **Çok Sayfalı Qt Arayüzü:** `QStackedWidget` mimarisiyle kurgulanmış kurallar ve yönlü fotoğraf inceleme pencereleri.
- **Dinamik Vektör Katman Yönetimi:** Tahmin edilen koordinatlar ile gerçek hedef noktayı harita üzerinde `memory` katmanları ve özel sembolojilerle anlık görselleştirme.
- **Jeodezik Mesafe Motoru:** Tahminler ile hedef arasındaki sapmayı düzlem geometrisi yerine **GRS80 elipsoidi** üzerinden `QgsDistanceArea` ile hesaplama (TUREF/ITRF uyumlu).
- **Çok Oyunculu Yarışma Mekaniği:** İki oyuncunun tahminlerini harita tuvali üzerinden toplayıp sapma farklarını ve kazananı raporlayan sonuç ekranı.

## 🧰 Kullanılan Teknolojiler & Kütüphaneler
- **Python 3**
- **PyQGIS API** (`QgsProject`, `QgsVectorLayer`, `QgsDistanceArea`, `QgsMapToolEmitPoint`)
- **PyQt5** (`QDialog`, `QStackedWidget`, `QPixmap`)
- **QGIS 3.x**

---
*Proje Sahibi & Sistem Tasarımı: Mustafa Şamil İngenç*  
*Kodlama & Teknik Dokümantasyon: Üretken Yapay Zeka (AI-Assisted)*
