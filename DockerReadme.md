# Docker Kullanım Kılavuzu - Fatura İşleme API

Bu belge, Fatura İşleme API projesinin Docker ile nasıl çalıştırılacağını ve PyCharm IDE'si üzerinden nasıl yönetileceğini açıklar.

## İçindekiler

1. [Gereksinimler](#gereksinimler)
2. [Docker ile Çalıştırma](#docker-ile-çalıştırma)
   - [Docker CLI ile Çalıştırma](#docker-cli-ile-çalıştırma)
   - [Docker Compose ile Çalıştırma](#docker-compose-ile-çalıştırma)
3. [PyCharm ile Docker Entegrasyonu](#pycharm-ile-docker-entegrasyonu)
   - [Docker Desteğini Etkinleştirme](#docker-desteğini-etkinleştirme)
   - [Docker Compose Yapılandırması](#docker-compose-yapılandırması)
   - [Docker Container'ında Python Interpreter Kullanma](#docker-containerında-python-interpreter-kullanma)
   - [Docker Container'ında Debug Yapma](#docker-containerında-debug-yapma)
4. [Sık Karşılaşılan Sorunlar](#sık-karşılaşılan-sorunlar)

## Gereksinimler

- [Docker](https://www.docker.com/products/docker-desktop/) (en az 20.10.x sürümü)
- [Docker Compose](https://docs.docker.com/compose/install/) (en az 2.x sürümü, Docker Desktop ile birlikte gelir)
- [PyCharm Professional](https://www.jetbrains.com/pycharm/download/) (Docker entegrasyonu için Professional sürüm gereklidir)

## Docker ile Çalıştırma

### Docker CLI ile Çalıştırma

1. Proje dizininde Docker imajını oluşturun:

```bash
docker build -t invoice-processor-api .
```

2. Docker container'ını çalıştırın:

```bash
docker run -p 8000:8000 -v ./test_images:/app/test_images invoice-processor-api
```

3. API'ye http://localhost:8000 adresinden erişebilirsiniz.
4. API dokümantasyonuna http://localhost:8000/docs adresinden erişebilirsiniz.

### Docker Compose ile Çalıştırma

1. Proje dizininde Docker Compose ile container'ı başlatın:

```bash
docker-compose up
```

2. Arka planda çalıştırmak için:

```bash
docker-compose up -d
```

3. Container'ı durdurmak için:

```bash
docker-compose down
```

4. API'ye http://localhost:8000 adresinden erişebilirsiniz.
5. API dokümantasyonuna http://localhost:8000/docs adresinden erişebilirsiniz.

## PyCharm ile Docker Entegrasyonu

### Docker Desteğini Etkinleştirme

1. PyCharm'ı açın ve projeyi yükleyin.
2. **File > Settings > Plugins** menüsüne gidin.
3. "Docker" eklentisinin yüklü olduğundan emin olun. Yüklü değilse, "Install" düğmesine tıklayarak yükleyin.
4. **File > Settings > Build, Execution, Deployment > Docker** menüsüne gidin.
5. "+" düğmesine tıklayarak yeni bir Docker bağlantısı ekleyin.
6. Docker Engine'in çalıştığı adresi belirtin (genellikle Windows'ta "tcp://localhost:2375" veya Unix soketleri).
7. "Apply" ve "OK" düğmelerine tıklayın.

### Docker Compose Yapılandırması

1. PyCharm'da **Run > Edit Configurations** menüsüne gidin.
2. "+" düğmesine tıklayın ve "Docker > Docker-compose" seçeneğini seçin.
3. Yapılandırmaya bir isim verin (örn. "Docker Compose").
4. "Compose files" alanında, proje dizinindeki `docker-compose.yml` dosyasını seçin.
5. "Services" alanında "invoice-processor" hizmetini seçin.
6. "Apply" ve "OK" düğmelerine tıklayın.
7. Artık PyCharm'ın üst kısmındaki çalıştırma yapılandırmaları açılır menüsünden "Docker Compose" seçeneğini seçebilir ve yeşil "Run" düğmesine tıklayarak Docker container'ını başlatabilirsiniz.

### Docker Container'ında Python Interpreter Kullanma

1. **File > Settings > Project > Python Interpreter** menüsüne gidin.
2. Dişli simgesine tıklayın ve "Add" seçeneğini seçin.
3. Sol panelde "Docker" seçeneğini seçin.
4. "Image name" alanında "invoice-processor-api" imajını seçin.
5. "Python interpreter path" alanında "/usr/local/bin/python" yazın.
6. "OK" düğmesine tıklayın.
7. Artık PyCharm, Docker container'ındaki Python yorumlayıcısını kullanacaktır.

### Docker Container'ında Debug Yapma

1. **Run > Edit Configurations** menüsüne gidin.
2. "+" düğmesine tıklayın ve "Python" seçeneğini seçin.
3. Yapılandırmaya bir isim verin (örn. "Debug in Docker").
4. "Script path" alanında "main.py" dosyasını seçin.
5. "Python interpreter" alanında, daha önce eklediğiniz Docker container'ındaki Python yorumlayıcısını seçin.
6. "Working directory" alanında proje dizinini seçin.
7. "Apply" ve "OK" düğmelerine tıklayın.
8. Kodunuzda breakpoint'ler ekleyin.
9. Artık PyCharm'ın üst kısmındaki çalıştırma yapılandırmaları açılır menüsünden "Debug in Docker" seçeneğini seçebilir ve yeşil "Debug" düğmesine tıklayarak Docker container'ında debug yapabilirsiniz.

## Sık Karşılaşılan Sorunlar

### Docker Container'ı Başlatılamıyor

- Docker servisinin çalıştığından emin olun.
- Port çakışması olup olmadığını kontrol edin. 8000 portu başka bir uygulama tarafından kullanılıyor olabilir.
- Docker imajını yeniden oluşturmayı deneyin: `docker-compose build --no-cache`

### PyCharm Docker Bağlantısı Kurulamıyor

- Docker Desktop'ın çalıştığından emin olun.
- Windows'ta "Expose daemon on tcp://localhost:2375 without TLS" seçeneğinin etkinleştirildiğinden emin olun (Docker Desktop > Settings > General).
- PyCharm'ı yeniden başlatmayı deneyin.

### Model Dosyaları Bulunamıyor

- Docker imajının doğru şekilde oluşturulduğundan emin olun.
- Dockerfile'da model dosyalarının doğru şekilde kopyalandığından emin olun.
- Docker container'ına bağlanarak dosyaların varlığını kontrol edin: `docker exec -it invoice-processor bash`