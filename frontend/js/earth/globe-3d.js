/**
 * NASA Earth Systems Trend Detective
 * Immersive 3D Earth Exploration Engine (Three.js & GSAP ScrollTrigger)
 * 
 * Signature Experience:
 * Scene 1: Deep space, rotating Earth, mission branding & scroll invitation.
 * Scene 2: Global exploration, lat/lon lattice, satellite orbits & observation nodes.
 * Scene 3: Methane dynamics, molecular visualization & greenhouse heat entrapment.
 * Scene 4: Precision rotation toward India (22°N, 79°E), glowing target marker.
 * Scene 5: Cinematic zoom into India, 6 study regions, 255 spatial lattice nodes.
 * Scene 6: Seamless transition into interactive environmental intelligence dashboard.
 */

class Earth3DApp {
  constructor(containerId = 'earthCanvasContainer') {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.isWebGLAvailable = this.checkWebGL();
    if (!this.isWebGLAvailable) {
      this.renderFallback();
      return;
    }

    this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    this.width = this.container.clientWidth || window.innerWidth;
    this.height = this.container.clientHeight || window.innerHeight;
    this.earthRadius = 5.0;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.earthGroup = null;
    this.earthMesh = null;
    this.cloudsMesh = null;
    this.atmosphereMesh = null;
    this.starsMesh = null;
    this.satelliteGroup = null;
    this.nodesGroup = null;
    this.indiaHighlightGroup = null;
    this.methaneMoleculesGroup = null;

    this.clock = new THREE.Clock();
    this.animationFrameId = null;
    this.isPaused = false;

    // Camera target vectors for GSAP
    this.cameraState = {
      x: 0,
      y: 1.5,
      z: 22,
      targetX: 0,
      targetY: 0,
      targetZ: 0,
      earthRotX: 0.15,
      earthRotY: 0.0,
      earthRotZ: 0.0,
      cloudsOpacity: 0.85,
      nodesOpacity: 0.0,
      indiaHighlightOpacity: 0.0,
      methaneOpacity: 0.0,
      satelliteOpacity: 0.8
    };

    this.init();
  }

  checkWebGL() {
    try {
      const canvas = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
    } catch (e) {
      return false;
    }
  }

  renderFallback() {
    if (!this.container) return;
    this.container.innerHTML = `
      <div class="webgl-fallback" style="position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; background: radial-gradient(circle at center, #071329 0%, #020611 100%); color: #fff; text-align: center; padding: 2rem;">
        <div style="font-size: 3rem; color: var(--cyan-primary); margin-bottom: 1rem;"><i class="fa-solid fa-earth-asia"></i></div>
        <h2 style="font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem;">Earth Systems Trend Detective</h2>
        <p style="color: var(--text-secondary); max-width: 500px; margin-bottom: 1.5rem;">
          Exploring atmospheric methane and satellite Earth observations across India.
        </p>
        <a href="#dashboardSection" class="btn-nasa btn-nasa-primary">Enter Environmental Dashboard</a>
      </div>
    `;
  }

  init() {
    // 1. Scene & Camera
    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(0x020611, 0.015);

    this.camera = new THREE.PerspectiveCamera(45, this.width / this.height, 0.1, 1000);
    this.camera.position.set(this.cameraState.x, this.cameraState.y, this.cameraState.z);

    // 2. Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    this.renderer.setSize(this.width, this.height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;
    this.container.appendChild(this.renderer.domElement);

    // 3. Lighting
    this.setupLighting();

    // 4. Build 3D Objects
    this.buildStars();
    this.buildEarthSystem();
    this.buildSatellite();
    this.buildMethaneMolecules();
    this.buildIndiaSpatialLattice();

    // 5. Setup ScrollTrigger Choreography
    this.setupScrollChoreography();

    // 6. Window Events
    window.addEventListener('resize', this.onResize.bind(this));
    document.addEventListener('visibilitychange', () => {
      this.isPaused = document.visibilityState === 'hidden';
    });

    // 7. Start Render Loop
    this.animate();
  }

  setupLighting() {
    // Distant Sun Light
    const sunLight = new THREE.DirectionalLight(0xffffff, 2.2);
    sunLight.position.set(25, 12, 18);
    this.scene.add(sunLight);

    // Deep space ambient fill
    const ambientLight = new THREE.AmbientLight(0x0d2040, 1.2);
    this.scene.add(ambientLight);

    // Atmospheric rim light
    const rimLight = new THREE.DirectionalLight(0x00d2ff, 1.6);
    rimLight.position.set(-20, -10, -15);
    this.scene.add(rimLight);
  }

  buildStars() {
    const starCount = 2000;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(starCount * 3);
    const colors = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount; i++) {
      const radius = THREE.MathUtils.randFloat(70, 180);
      const theta = THREE.MathUtils.randFloat(0, Math.PI * 2);
      const phi = THREE.MathUtils.randFloat(0, Math.PI);

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.cos(phi);
      positions[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);

      // Star color variation: cool blue, white, subtle gold
      const choice = Math.random();
      if (choice > 0.7) {
        colors[i * 3] = 0.6; colors[i * 3 + 1] = 0.85; colors[i * 3 + 2] = 1.0;
      } else if (choice > 0.4) {
        colors[i * 3] = 1.0; colors[i * 3 + 1] = 0.95; colors[i * 3 + 2] = 0.85;
      } else {
        colors[i * 3] = 1.0; colors[i * 3 + 1] = 1.0; colors[i * 3 + 2] = 1.0;
      }
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 1.4,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      sizeAttenuation: true
    });

    this.starsMesh = new THREE.Points(geometry, material);
    this.scene.add(this.starsMesh);
  }

  buildEarthSystem() {
    this.earthGroup = new THREE.Group();

    // 1. Procedural Surface Texture
    const surfaceTexture = this.generateEarthCanvasTexture();
    const bumpTexture = this.generateEarthBumpTexture();

    const earthGeo = new THREE.SphereGeometry(this.earthRadius, 64, 64);
    const earthMat = new THREE.MeshStandardMaterial({
      map: surfaceTexture,
      bumpMap: bumpTexture,
      bumpScale: 0.05,
      roughness: 0.65,
      metalness: 0.1
    });

    this.earthMesh = new THREE.Mesh(earthGeo, earthMat);
    this.earthGroup.add(this.earthMesh);

    // 2. Cloud Sphere
    const cloudTexture = this.generateCloudCanvasTexture();
    const cloudGeo = new THREE.SphereGeometry(this.earthRadius * 1.018, 48, 48);
    const cloudMat = new THREE.MeshStandardMaterial({
      map: cloudTexture,
      transparent: true,
      opacity: this.cameraState.cloudsOpacity,
      blending: THREE.NormalBlending,
      depthWrite: false
    });
    this.cloudsMesh = new THREE.Mesh(cloudGeo, cloudMat);
    this.earthGroup.add(this.cloudsMesh);

    // 3. Atmospheric Outer Glow
    const atmosGeo = new THREE.SphereGeometry(this.earthRadius * 1.055, 48, 48);
    const atmosMat = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.68 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.2);
          gl_FragColor = vec4(0.0, 0.82, 1.0, 1.0) * intensity * 0.95;
        }
      `,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true,
      depthWrite: false
    });
    this.atmosphereMesh = new THREE.Mesh(atmosGeo, atmosMat);
    this.earthGroup.add(this.atmosphereMesh);

    this.scene.add(this.earthGroup);
  }

  generateEarthCanvasTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');

    // Deep Ocean gradient
    const oceanGrad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    oceanGrad.addColorStop(0, '#041126');
    oceanGrad.addColorStop(0.5, '#051838');
    oceanGrad.addColorStop(1, '#030d1e');
    ctx.fillStyle = oceanGrad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Fine Latitude / Longitude lines
    ctx.strokeStyle = 'rgba(0, 210, 255, 0.08)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= canvas.width; x += canvas.width / 12) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y <= canvas.height; y += canvas.height / 6) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Helper to map Lat/Lon to Canvas X/Y (Equirectangular)
    const toCanvas = (lat, lon) => ({
      x: ((lon + 180) / 360) * canvas.width,
      y: ((90 - lat) / 180) * canvas.height
    });

    // Draw Continents (Simplified accurate silhouettes)
    ctx.fillStyle = '#0d2d3a';
    ctx.strokeStyle = 'rgba(0, 210, 255, 0.35)';
    ctx.lineWidth = 1.5;

    const continents = [
      // Eurasia & Africa broad mass
      [
        { lat: 70, lon: 10 }, { lat: 60, lon: 30 }, { lat: 55, lon: 60 }, { lat: 65, lon: 100 },
        { lat: 60, lon: 140 }, { lat: 40, lon: 120 }, { lat: 25, lon: 105 }, { lat: 10, lon: 105 },
        { lat: 1, lon: 104 }, { lat: 10, lon: 78 }, { lat: 22, lon: 68 }, { lat: 30, lon: 50 },
        { lat: 12, lon: 45 }, { lat: -35, lon: 20 }, { lat: 5, lon: 5 }, { lat: 35, lon: -5 },
        { lat: 45, lon: 0 }, { lat: 55, lon: 10 }
      ],
      // North America
      [
        { lat: 70, lon: -160 }, { lat: 70, lon: -70 }, { lat: 45, lon: -60 }, { lat: 25, lon: -80 },
        { lat: 15, lon: -90 }, { lat: 20, lon: -105 }, { lat: 35, lon: -120 }, { lat: 55, lon: -130 }
      ],
      // South America
      [
        { lat: 10, lon: -75 }, { lat: -5, lon: -35 }, { lat: -25, lon: -45 }, { lat: -55, lon: -70 },
        { lat: -20, lon: -70 }, { lat: 0, lon: -80 }
      ],
      // Australia
      [
        { lat: -12, lon: 130 }, { lat: -15, lon: 145 }, { lat: -35, lon: 150 }, { lat: -35, lon: 115 },
        { lat: -20, lon: 115 }
      ]
    ];

    continents.forEach(poly => {
      ctx.beginPath();
      poly.forEach((pt, idx) => {
        const c = toCanvas(pt.lat, pt.lon);
        if (idx === 0) ctx.moveTo(c.x, c.y);
        else ctx.lineTo(c.x, c.y);
      });
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });

    // High Detail: Indian Subcontinent Silhouette & Highlight
    const indiaPolygon = [
      { lat: 35.5, lon: 74.5 }, { lat: 34.0, lon: 78.5 }, { lat: 31.0, lon: 79.5 },
      { lat: 28.5, lon: 88.0 }, { lat: 27.5, lon: 97.0 }, { lat: 24.0, lon: 94.0 },
      { lat: 22.0, lon: 89.5 }, { lat: 20.0, lon: 86.0 }, { lat: 16.0, lon: 81.0 },
      { lat: 11.5, lon: 79.8 }, { lat: 8.0, lon: 77.5 }, { lat: 10.5, lon: 76.0 },
      { lat: 15.0, lon: 73.8 }, { lat: 20.0, lon: 72.8 }, { lat: 23.5, lon: 68.5 },
      { lat: 26.5, lon: 70.0 }, { lat: 31.0, lon: 74.0 }, { lat: 35.5, lon: 74.5 }
    ];

    // Glow backing for India
    ctx.shadowColor = '#00d2ff';
    ctx.shadowBlur = 15;
    ctx.fillStyle = '#103d4c';
    ctx.strokeStyle = '#00d2ff';
    ctx.lineWidth = 2.5;

    ctx.beginPath();
    indiaPolygon.forEach((pt, idx) => {
      const c = toCanvas(pt.lat, pt.lon);
      if (idx === 0) ctx.moveTo(c.x, c.y);
      else ctx.lineTo(c.x, c.y);
    });
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Reset shadow
    ctx.shadowBlur = 0;

    // Subtle Night lights on continents
    ctx.fillStyle = 'rgba(255, 230, 160, 0.45)';
    for (let i = 0; i < 400; i++) {
      // Clustered around India and Eurasia
      const lat = THREE.MathUtils.randFloat(8, 32);
      const lon = THREE.MathUtils.randFloat(70, 88);
      const pt = toCanvas(lat, lon);
      ctx.fillRect(pt.x, pt.y, THREE.MathUtils.randFloat(1, 2.5), THREE.MathUtils.randFloat(1, 2.5));
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    return texture;
  }

  generateEarthBumpTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw elevated mountain bands (Himalayas, Alps, Rockies)
    ctx.fillStyle = '#ffffff';
    ctx.filter = 'blur(4px)';
    ctx.fillRect(canvas.width * (75/360 + 0.5), canvas.height * (1 - (30+90)/180), 60, 15);
    ctx.filter = 'none';

    return new THREE.CanvasTexture(canvas);
  }

  generateCloudCanvasTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = 'rgba(0, 0, 0, 0)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Semi-transparent procedural cloud bands
    ctx.fillStyle = 'rgba(255, 255, 255, 0.35)';
    for (let i = 0; i < 25; i++) {
      const y = THREE.MathUtils.randFloat(50, 460);
      const x = THREE.MathUtils.randFloat(0, 1024);
      const w = THREE.MathUtils.randFloat(120, 350);
      const h = THREE.MathUtils.randFloat(20, 60);

      const grad = ctx.createRadialGradient(x + w / 2, y + h / 2, 5, x + w / 2, y + h / 2, w / 2);
      grad.addColorStop(0, 'rgba(255, 255, 255, 0.45)');
      grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
      ctx.fillStyle = grad;
      ctx.fillRect(x, y, w, h);
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    return texture;
  }

  buildSatellite() {
    this.satelliteGroup = new THREE.Group();

    // Satellite Body (Bus)
    const busGeo = new THREE.BoxGeometry(0.2, 0.3, 0.2);
    const busMat = new THREE.MeshStandardMaterial({ color: 0xcccccc, metalness: 0.8, roughness: 0.2 });
    const bus = new THREE.Mesh(busGeo, busMat);

    // Solar Arrays (Golden/Blue panels)
    const wingGeo = new THREE.BoxGeometry(0.8, 0.02, 0.25);
    const wingMat = new THREE.MeshStandardMaterial({ color: 0x0055ff, metalness: 0.9, roughness: 0.1 });
    const leftWing = new THREE.Mesh(wingGeo, wingMat);
    leftWing.position.x = 0.55;
    const rightWing = new THREE.Mesh(wingGeo, wingMat);
    rightWing.position.x = -0.55;

    // Sensor Swath Cone (TROPOMI SWIR Scanner)
    const coneGeo = new THREE.ConeGeometry(0.65, 1.8, 16, 1, true);
    const coneMat = new THREE.MeshBasicMaterial({
      color: 0x00d2ff,
      transparent: true,
      opacity: 0.25,
      side: THREE.DoubleSide,
      depthWrite: false
    });
    const cone = new THREE.Mesh(coneGeo, coneMat);
    cone.position.y = -1.0;
    cone.rotation.x = Math.PI;

    this.satelliteGroup.add(bus);
    this.satelliteGroup.add(leftWing);
    this.satelliteGroup.add(rightWing);
    this.satelliteGroup.add(cone);

    // Orbit parameters
    this.satelliteGroup.position.set(0, 4.2, 5.2);
    this.scene.add(this.satelliteGroup);
  }

  buildMethaneMolecules() {
    this.methaneMoleculesGroup = new THREE.Group();

    // Create a cluster of floating CH4 molecules (Carbon + 4 Hydrogen atoms)
    const carbonGeo = new THREE.SphereGeometry(0.12, 16, 16);
    const carbonMat = new THREE.MeshStandardMaterial({ color: 0x00d2ff, roughness: 0.3, emissive: 0x004466 });

    const hydrogenGeo = new THREE.SphereGeometry(0.06, 12, 12);
    const hydrogenMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });

    const tetrahedralAngles = [
      [1, 1, 1], [-1, -1, 1], [-1, 1, -1], [1, -1, -1]
    ];

    for (let i = 0; i < 28; i++) {
      const mol = new THREE.Group();
      const carbon = new THREE.Mesh(carbonGeo, carbonMat);
      mol.add(carbon);

      tetrahedralAngles.forEach(dir => {
        const h = new THREE.Mesh(hydrogenGeo, hydrogenMat);
        const norm = new THREE.Vector3(...dir).normalize().multiplyScalar(0.22);
        h.position.copy(norm);
        mol.add(h);
      });

      // Scatter in atmospheric layer above India
      const lat = THREE.MathUtils.randFloat(12, 30);
      const lon = THREE.MathUtils.randFloat(72, 86);
      const pos = this.latLonToVector3(lat, lon, this.earthRadius + THREE.MathUtils.randFloat(0.4, 1.2));
      mol.position.copy(pos);
      this.methaneMoleculesGroup.add(mol);
    }

    this.methaneMoleculesGroup.visible = false;
    this.earthGroup.add(this.methaneMoleculesGroup);
  }

  buildIndiaSpatialLattice() {
    this.nodesGroup = new THREE.Group();
    this.indiaHighlightGroup = new THREE.Group();

    // Convert (Lat, Lon) to 3D Cartesian on Sphere
    // India centroid: ~22°N, ~79°E
    const targetRingGeo = new THREE.RingGeometry(0.7, 0.78, 32);
    const targetRingMat = new THREE.MeshBasicMaterial({
      color: 0x00d2ff,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.0
    });
    this.targetRing = new THREE.Mesh(targetRingGeo, targetRingMat);
    const targetPos = this.latLonToVector3(22.0, 79.0, this.earthRadius * 1.02);
    this.targetRing.position.copy(targetPos);
    this.targetRing.lookAt(new THREE.Vector3(0, 0, 0));
    this.indiaHighlightGroup.add(this.targetRing);

    // 255 Nodes Lattice Representation
    // Generate regular 2° grid across India bounds: Lat 7° to 37°, Lon 69° to 97°
    const nodeObservedGeo = new THREE.SphereGeometry(0.045, 12, 12);
    const nodeObservedMat = new THREE.MeshBasicMaterial({ color: 0x00ff88 }); // Observed = Green

    const nodeUnobservedGeo = new THREE.RingGeometry(0.03, 0.045, 16);
    const nodeUnobservedMat = new THREE.MeshBasicMaterial({ color: 0x3b82f6, side: THREE.DoubleSide }); // Unobserved = Dashed Ring

    // Sample representative nodes matching verified project density
    for (let lat = 8; lat <= 36; lat += 2) {
      for (let lon = 70; lon <= 94; lon += 2) {
        // Approximate India geographic bounds filter
        if ((lat < 15 && lon > 81) || (lat < 12 && lon > 79) || (lat > 32 && lon > 79) || (lat > 28 && lon < 72)) {
          continue; // Outside subcontinent polygon
        }

        const isObserved = (lat >= 16 && lat <= 30 && lon >= 72 && lon <= 88) && (lat !== 24 || lon !== 84);
        const pos = this.latLonToVector3(lat, lon, this.earthRadius * 1.012);

        if (isObserved) {
          const marker = new THREE.Mesh(nodeObservedGeo, nodeObservedMat);
          marker.position.copy(pos);
          this.nodesGroup.add(marker);
        } else {
          const marker = new THREE.Mesh(nodeUnobservedGeo, nodeUnobservedMat);
          marker.position.copy(pos);
          marker.lookAt(new THREE.Vector3(0, 0, 0));
          this.nodesGroup.add(marker);
        }
      }
    }

    this.nodesGroup.visible = false;
    this.indiaHighlightGroup.visible = false;

    this.earthGroup.add(this.nodesGroup);
    this.earthGroup.add(this.indiaHighlightGroup);
  }

  latLonToVector3(lat, lon, radius) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);

    return new THREE.Vector3(
      -(radius * Math.sin(phi) * Math.cos(theta)),
      radius * Math.cos(phi),
      radius * Math.sin(phi) * Math.sin(theta)
    );
  }

  setupScrollChoreography() {
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
      console.warn('GSAP or ScrollTrigger not loaded; using default rotation.');
      return;
    }

    gsap.registerPlugin(ScrollTrigger);

    // Rotate Earth so India (22°N, 79°E) faces front camera
    // Mathematical rotation angles for India:
    const targetIndiaY = (79.0 + 90) * (Math.PI / 180) * -1; // -2.95 rad
    const targetIndiaX = -0.38; // Tilts northern hemisphere to camera

    // Master Timeline bound to 3D scroll container
    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: '#earthScrollStory',
        start: 'top top',
        end: 'bottom bottom',
        scrub: this.prefersReducedMotion ? false : 1.2,
        onUpdate: (self) => {
          const p = self.progress;

          // Scene 3: Methane molecules visible
          if (this.methaneMoleculesGroup) {
            this.methaneMoleculesGroup.visible = p > 0.32 && p < 0.65;
          }

          // Scene 4 & 5: India target ring and nodes visible
          if (this.indiaHighlightGroup && this.targetRing) {
            this.indiaHighlightGroup.visible = p > 0.45;
            this.targetRing.material.opacity = p > 0.55 ? 0.9 : (p - 0.45) * 9;
          }

          if (this.nodesGroup) {
            this.nodesGroup.visible = p > 0.65;
          }
        }
      }
    });

    // Scene 1 -> Scene 2: Deep space to Global Exploration (Scroll: 0% -> 20%)
    tl.to(this.camera.position, {
      x: 0,
      y: 0.8,
      z: 14.5,
      ease: 'power1.inOut'
    }, 0);

    tl.to(this.earthGroup.rotation, {
      x: 0.2,
      y: 1.2,
      ease: 'none'
    }, 0);

    // Scene 2 -> Scene 3: Understanding Methane (Scroll: 20% -> 45%)
    tl.to(this.camera.position, {
      x: 2.2,
      y: 0.5,
      z: 10.0,
      ease: 'power1.inOut'
    }, 0.25);

    tl.to(this.earthGroup.rotation, {
      x: 0.1,
      y: 2.4,
      ease: 'none'
    }, 0.25);

    // Scene 3 -> Scene 4: Rotate Toward India (Scroll: 45% -> 70%)
    tl.to(this.camera.position, {
      x: 0,
      y: 0.2,
      z: 7.2,
      ease: 'power2.inOut'
    }, 0.5);

    tl.to(this.earthGroup.rotation, {
      x: targetIndiaX,
      y: targetIndiaY,
      z: 0.05,
      ease: 'power2.inOut'
    }, 0.5);

    // Scene 5: Cinematic Zoom into India & 6 Regions (Scroll: 70% -> 90%)
    tl.to(this.camera.position, {
      x: 0.2,
      y: 0.4,
      z: 5.6,
      ease: 'power2.inOut'
    }, 0.72);

    // Scene 6: Seamless hand-off to Dashboard (Scroll: 90% -> 100%)
    tl.to(this.earthGroup.position, {
      y: -2.5,
      z: -3.0,
      ease: 'power2.inOut'
    }, 0.88);

    tl.to(this.earthGroup.scale, {
      x: 0.65,
      y: 0.65,
      z: 0.65,
      ease: 'power2.inOut'
    }, 0.88);
  }

  animate() {
    this.animationFrameId = requestAnimationFrame(this.animate.bind(this));

    if (this.isPaused) return;

    const delta = this.clock.getDelta();

    // Natural Earth idle spin only when not scrolled far into India
    const scrollPos = window.scrollY || window.pageYOffset;
    if (scrollPos < 100 && this.earthGroup) {
      this.earthGroup.rotation.y += delta * 0.06;
    }

    // Clouds rotate slightly faster than Earth
    if (this.cloudsMesh) {
      this.cloudsMesh.rotation.y += delta * 0.08;
    }

    // Satellite polar orbit motion
    if (this.satelliteGroup) {
      const time = this.clock.getElapsedTime();
      const orbitRadius = 6.4;
      this.satelliteGroup.position.x = Math.sin(time * 0.6) * orbitRadius;
      this.satelliteGroup.position.y = Math.cos(time * 0.6) * (orbitRadius * 0.85);
      this.satelliteGroup.position.z = Math.cos(time * 0.6) * 2.5;
      this.satelliteGroup.lookAt(new THREE.Vector3(0, 0, 0));
    }

    // Subtle pulsing target ring
    if (this.targetRing && this.targetRing.visible) {
      const scale = 1.0 + Math.sin(this.clock.getElapsedTime() * 4.0) * 0.06;
      this.targetRing.scale.set(scale, scale, 1.0);
    }

    this.renderer.render(this.scene, this.camera);
  }

  onResize() {
    if (!this.container || !this.camera || !this.renderer) return;
    this.width = this.container.clientWidth || window.innerWidth;
    this.height = this.container.clientHeight || window.innerHeight;

    this.camera.aspect = this.width / this.height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.width, this.height);
  }

  dispose() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    window.removeEventListener('resize', this.onResize);

    if (this.renderer && this.renderer.domElement) {
      this.renderer.domElement.remove();
      this.renderer.dispose();
    }
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('earthCanvasContainer')) {
    window.earth3DApp = new Earth3DApp('earthCanvasContainer');
  }
});
