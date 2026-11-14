/**
 * NASA Earth Systems Trend Detective — 3D Earth & Procedural Globe
 * Three.js Implementation with Atmosphere & Fly-To Camera
 */

class EarthVisualizer {
  constructor(canvasId = 'earth-canvas') {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.globe = null;
    this.clouds = null;
    this.atmosphere = null;
    this.stars = null;
    this.markerGroup = null;

    this.isFlying = false;
    this.isDragging = false;
    this.previousMousePosition = { x: 0, y: 0 };

    this.init();
  }

  init() {
    const width = this.canvas.parentElement.clientWidth;
    const height = this.canvas.parentElement.clientHeight;

    // 1. Scene & Camera
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    this.camera.position.set(0, 0, 3.2);

    // 2. Renderer
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(0x334155, 1.2);
    this.scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, 2.0);
    sunLight.position.set(5, 3, 5);
    this.scene.add(sunLight);

    const cyanRim = new THREE.PointLight(0x00f2fe, 1.5, 10);
    cyanRim.position.set(-4, -2, -2);
    this.scene.add(cyanRim);

    // 4. Procedural Earth Texture
    const earthTexture = this.generateEarthTexture();
    const globeGeo = new THREE.SphereGeometry(1, 64, 64);
    const globeMat = new THREE.MeshPhongMaterial({
      map: earthTexture,
      bumpScale: 0.05,
      specular: new THREE.Color(0x1e293b),
      shininess: 15
    });
    this.globe = new THREE.Mesh(globeGeo, globeMat);
    this.scene.add(this.globe);

    // 5. Atmosphere Glow Shell
    const atmoGeo = new THREE.SphereGeometry(1.025, 64, 64);
    const atmoMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      transparent: true,
      opacity: 0.15,
      side: THREE.BackSide
    });
    this.atmosphere = new THREE.Mesh(atmoGeo, atmoMat);
    this.scene.add(this.atmosphere);

    // 6. Starfield
    this.createStarfield();

    // 7. India Marker & Graph Nodes
    this.markerGroup = new THREE.Group();
    this.globe.add(this.markerGroup);
    this.addIndiaPulseMarker();

    // 8. Event Listeners
    window.addEventListener('resize', () => this.onWindowResize());
    this.setupInteractions();

    // 9. Initial rotation to face Indian Ocean / India
    this.globe.rotation.y = -1.8;
    this.globe.rotation.x = 0.3;

    // Start Animation Loop
    this.animate();
  }

  generateEarthTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');

    // Deep Ocean
    ctx.fillStyle = '#060d1d';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Latitude & Longitude Grid Graticules
    ctx.strokeStyle = 'rgba(0, 242, 254, 0.08)';
    ctx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += 64) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 64) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Continents & Landmasses representation (approximate polygons)
    ctx.fillStyle = '#112240';
    ctx.strokeStyle = '#00f2fe';
    ctx.lineWidth = 2;

    // India Subcontinent region
    // Lon 68-98 deg E -> X: (68+180)/360 * 2048 ~ 1410
    // Lat 8-38 deg N -> Y: (90-25)/180 * 1024 ~ 370
    ctx.beginPath();
    ctx.moveTo(1410, 310);
    ctx.lineTo(1530, 330);
    ctx.lineTo(1490, 480);
    ctx.lineTo(1450, 520); // southern tip Kanyakumari
    ctx.lineTo(1410, 430);
    ctx.lineTo(1380, 360);
    ctx.closePath();
    ctx.fillStyle = '#1e3a5f';
    ctx.fill();
    ctx.stroke();

    // Eurasian mass
    ctx.beginPath();
    ctx.moveTo(1100, 250);
    ctx.lineTo(1700, 200);
    ctx.lineTo(1650, 450);
    ctx.lineTo(1350, 350);
    ctx.closePath();
    ctx.fillStyle = '#132847';
    ctx.fill();

    // Africa
    ctx.beginPath();
    ctx.moveTo(1000, 350);
    ctx.lineTo(1200, 380);
    ctx.lineTo(1180, 600);
    ctx.lineTo(1050, 550);
    ctx.closePath();
    ctx.fillStyle = '#132847';
    ctx.fill();

    // Americas
    ctx.beginPath();
    ctx.moveTo(400, 200);
    ctx.lineTo(600, 250);
    ctx.lineTo(550, 450);
    ctx.lineTo(450, 400);
    ctx.closePath();
    ctx.fillStyle = '#132847';
    ctx.fill();

    return new THREE.CanvasTexture(canvas);
  }

  createStarfield() {
    const starGeo = new THREE.BufferGeometry();
    const starCount = 1500;
    const positions = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 50;
      positions[i + 1] = (Math.random() - 0.5) * 50;
      positions[i + 2] = (Math.random() - 0.5) * 50;
    }

    starGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const starMat = new THREE.PointsMaterial({
      color: 0x94a3b8,
      size: 0.08,
      transparent: true,
      opacity: 0.6
    });

    this.stars = new THREE.Points(starGeo, starMat);
    this.scene.add(this.stars);
  }

  latLonToVector3(lat, lon, radius = 1.01) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);

    const x = -(radius * Math.sin(phi) * Math.cos(theta));
    const z = radius * Math.sin(phi) * Math.sin(theta);
    const y = radius * Math.cos(phi);

    return new THREE.Vector3(x, y, z);
  }

  addIndiaPulseMarker() {
    // Center of India: ~22°N, 79°E
    const pos = this.latLonToVector3(22.0, 79.0, 1.02);

    const ringGeo = new THREE.RingGeometry(0.02, 0.04, 32);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.9
    });

    const marker = new THREE.Mesh(ringGeo, ringMat);
    marker.position.copy(pos);
    marker.lookAt(new THREE.Vector3(0, 0, 0));
    this.markerGroup.add(marker);
    this.pulseMarker = marker;
  }

  setupInteractions() {
    const el = this.canvas;

    el.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.previousMousePosition = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
    });

    el.addEventListener('mousemove', (e) => {
      if (!this.isDragging || this.isFlying) return;

      const deltaX = e.clientX - this.previousMousePosition.x;
      const deltaY = e.clientY - this.previousMousePosition.y;

      this.globe.rotation.y += deltaX * 0.005;
      this.globe.rotation.x += deltaY * 0.005;

      this.previousMousePosition = { x: e.clientX, y: e.clientY };
    });
  }

  flyToIndia(callback) {
    if (this.isFlying) return;
    this.isFlying = true;

    // Target rotation to bring India (Lat 22°N, Lon 79°E) to front center
    const targetRotY = -1.45;
    const targetRotX = 0.38;
    const targetCamZ = 2.0;

    const startRotY = this.globe.rotation.y;
    const startRotX = this.globe.rotation.x;
    const startCamZ = this.camera.position.z;

    let progress = 0;
    const step = () => {
      progress += 0.02;
      const ease = 0.5 - Math.cos(progress * Math.PI) / 2;

      this.globe.rotation.y = startRotY + (targetRotY - startRotY) * ease;
      this.globe.rotation.x = startRotX + (targetRotX - startRotX) * ease;
      this.camera.position.z = startCamZ + (targetCamZ - startCamZ) * ease;

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        this.isFlying = false;
        if (callback) callback();
      }
    };
    step();
  }

  onWindowResize() {
    if (!this.canvas || !this.renderer || !this.camera) return;
    const width = this.canvas.parentElement.clientWidth;
    const height = this.canvas.parentElement.clientHeight;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    // Gentle idle spin if not dragging or flying
    if (!this.isDragging && !this.isFlying && this.globe) {
      this.globe.rotation.y += 0.001;
    }

    // Pulse marker effect
    if (this.pulseMarker) {
      const time = Date.now() * 0.003;
      const scale = 1 + Math.sin(time) * 0.25;
      this.pulseMarker.scale.set(scale, scale, 1);
    }

    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
  }
}

window.EarthVisualizer = EarthVisualizer;
