/**
 * CRICBRAIN - 3D Cricket World & Parallax Animation
 * Features:
 * - 3D Spinning Cricket Ball (leather texture + white stitching seam)
 * - Parallax mouse/touch tilt interaction
 * - Floating cricket stumps, bails, and willow bat in background
 * - 3D perspective pitch strip that moves with scroll
 * - Fallback to CSS-only 3D if WebGL is unavailable or prefers-reduced-motion is active
 */

(function () {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const container = document.getElementById("canvas-3d-container");
    const pitchStrip = document.getElementById("pitch-strip-element");

    let mouseX = 0;
    let mouseY = 0;
    let targetRotationX = 0;
    let targetRotationY = 0;

    // Track mouse / touch position for parallax
    window.addEventListener("mousemove", (e) => {
        if (prefersReducedMotion) return;
        const halfW = window.innerWidth / 2;
        const halfH = window.innerHeight / 2;
        mouseX = (e.clientX - halfW) / halfW;
        mouseY = (e.clientY - halfH) / halfH;
    });

    window.addEventListener("touchmove", (e) => {
        if (prefersReducedMotion || !e.touches[0]) return;
        const halfW = window.innerWidth / 2;
        const halfH = window.innerHeight / 2;
        mouseX = (e.touches[0].clientX - halfW) / halfW;
        mouseY = (e.touches[0].clientY - halfH) / halfH;
    }, { passive: true });

    // Perspective pitch strip scroll handler
    window.addEventListener("scroll", () => {
        if (!pitchStrip) return;
        const scrollY = window.scrollY || window.pageYOffset;
        const maxScroll = document.body.scrollHeight - window.innerHeight;
        const progress = Math.min(scrollY / (maxScroll || 1), 1);
        
        if (!prefersReducedMotion) {
            const tilt = 55 - (progress * 15);
            const translateY = scrollY * 0.15;
            pitchStrip.style.transform = `perspective(800px) rotateX(${tilt}deg) translateY(${translateY}px)`;
        }
    });

    // Check WebGL availability
    function isWebGLAvailable() {
        try {
            const canvas = document.createElement("canvas");
            return !!(window.WebGLRenderingContext && (canvas.getContext("webgl") || canvas.getContext("experimental-webgl")));
        } catch (e) {
            return false;
        }
    }

    if (!isWebGLAvailable() || typeof THREE === "undefined" || prefersReducedMotion) {
        initCssFallback();
        return;
    }

    // Init Three.js 3D Scene
    let scene, camera, renderer;
    let ballMesh, seamMesh;
    let batGroup, stumpsGroup;
    let clock;

    try {
        clock = new THREE.Clock();
        scene = new THREE.Scene();

        camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 0, 10);

        renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        // Stadium Floodlight 1 (Top Left)
        const floodLight1 = new THREE.SpotLight(0xfff1cc, 2.0);
        floodLight1.position.set(-8, 12, 10);
        floodLight1.angle = Math.PI / 4;
        floodLight1.penumbra = 0.5;
        scene.add(floodLight1);

        // Stadium Floodlight 2 (Top Right - Crisp Cyan/White)
        const floodLight2 = new THREE.SpotLight(0xdcf8ff, 1.8);
        floodLight2.position.set(8, 10, 8);
        floodLight2.angle = Math.PI / 4;
        floodLight2.penumbra = 0.5;
        scene.add(floodLight2);

        // Subtle Pitch Green Rim Light
        const greenRimLight = new THREE.DirectionalLight(0x10b981, 0.8);
        greenRimLight.position.set(0, -6, -4);
        scene.add(greenRimLight);

        // 1. CREATE 3D CRICKET BALL
        createCricketBall();

        // 2. CREATE FLOATING CRICKET BAT
        createCricketBat();

        // 3. CREATE FLOATING STUMPS & BAILS
        createCricketStumps();

        // Resize handler
        window.addEventListener("resize", onWindowResize);

        // Start Animation Loop
        animate();
    } catch (err) {
        console.warn("Three.js setup encountered error, using CSS fallback:", err);
        initCssFallback();
    }

    function createCricketBall() {
        const ballRadius = 1.7;
        const sphereGeo = new THREE.SphereGeometry(ballRadius, 64, 64);

        // Create realistic leather texture procedurally via canvas
        const leatherCanvas = document.createElement("canvas");
        leatherCanvas.width = 512;
        leatherCanvas.height = 512;
        const ctx = leatherCanvas.getContext("2d");

        // Rich cricket-ball red gradient
        const grad = ctx.createRadialGradient(256, 256, 10, 256, 256, 256);
        grad.addColorStop(0, "#ba1c1c");
        grad.addColorStop(0.5, "#991414");
        grad.addColorStop(1, "#660c0c");
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 512, 512);

        // Add subtle leather grain texture
        ctx.fillStyle = "rgba(0, 0, 0, 0.07)";
        for (let i = 0; i < 4000; i++) {
            const rx = Math.random() * 512;
            const ry = Math.random() * 512;
            ctx.fillRect(rx, ry, 1, 1);
        }

        // Gold lettering on the ball
        ctx.font = "bold 22px 'Space Grotesk', sans-serif";
        ctx.fillStyle = "rgba(255, 215, 0, 0.4)";
        ctx.textAlign = "center";
        ctx.fillText("CRICBRAIN", 256, 230);
        ctx.font = "14px 'Space Grotesk', sans-serif";
        ctx.fillText("SPECIAL MATCH BALL", 256, 260);

        const ballTexture = new THREE.CanvasTexture(leatherCanvas);

        const ballMat = new THREE.MeshStandardMaterial({
            map: ballTexture,
            roughness: 0.28,
            metalness: 0.15,
            color: 0xaa1c1c
        });

        ballMesh = new THREE.Mesh(sphereGeo, ballMat);
        ballMesh.position.set(0, 0.2, 2.5);
        scene.add(ballMesh);

        // White raised seam with stitches
        const seamGeo = new THREE.TorusGeometry(ballRadius + 0.02, 0.045, 16, 120);
        const seamMat = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            roughness: 0.5,
            metalness: 0.1
        });
        seamMesh = new THREE.Mesh(seamGeo, seamMat);
        seamMesh.rotation.x = Math.PI / 2;
        ballMesh.add(seamMesh);

        // Additional stitch dots along seam
        const stitchCount = 48;
        const stitchMat = new THREE.MeshBasicMaterial({ color: 0xeeeeee });
        for (let i = 0; i < stitchCount; i++) {
            const angle = (i / stitchCount) * Math.PI * 2;
            const stitchGeo = new THREE.BoxGeometry(0.02, 0.08, 0.03);
            const stitch = new THREE.Mesh(stitchGeo, stitchMat);
            const x = Math.cos(angle) * (ballRadius + 0.03);
            const y = Math.sin(angle) * (ballRadius + 0.03);
            stitch.position.set(x, y, 0);
            stitch.rotation.z = angle + Math.PI / 2;
            seamMesh.add(stitch);
        }
    }

    function createCricketBat() {
        batGroup = new THREE.Group();

        // Bat blade (willow wood)
        const bladeGeo = new THREE.BoxGeometry(0.55, 2.8, 0.15);
        const bladeMat = new THREE.MeshStandardMaterial({
            color: 0xdeb887, // Burlywood / English willow
            roughness: 0.6,
            metalness: 0.05
        });
        const blade = new THREE.Mesh(bladeGeo, bladeMat);
        blade.position.y = -0.4;
        batGroup.add(blade);

        // Bat handle (cane with rubber grip)
        const handleGeo = new THREE.CylinderGeometry(0.08, 0.08, 1.3, 16);
        const handleMat = new THREE.MeshStandardMaterial({
            color: 0x111111, // Black rubber grip
            roughness: 0.8
        });
        const handle = new THREE.Mesh(handleGeo, handleMat);
        handle.position.y = 1.5;
        batGroup.add(handle);

        // Colored handle coil rings
        const ringGeo = new THREE.TorusGeometry(0.085, 0.015, 8, 16);
        const ringMat = new THREE.MeshBasicMaterial({ color: 0xeab308 });
        const ring1 = new THREE.Mesh(ringGeo, ringMat);
        ring1.position.y = 1.2;
        ring1.rotation.x = Math.PI / 2;
        batGroup.add(ring1);

        // Position bat floating on the right side of the background
        batGroup.position.set(5.5, -0.5, -2);
        batGroup.rotation.z = 0.35;
        batGroup.rotation.y = -0.4;
        batGroup.scale.set(0.9, 0.9, 0.9);
        scene.add(batGroup);
    }

    function createCricketStumps() {
        stumpsGroup = new THREE.Group();
        const stumpMat = new THREE.MeshStandardMaterial({
            color: 0xcd853f, // Ash / hardwood
            roughness: 0.5
        });

        const stumpHeight = 2.4;
        const stumpRadius = 0.07;
        const spacing = 0.38;

        // 3 Stumps
        for (let i = -1; i <= 1; i++) {
            const stumpGeo = new THREE.CylinderGeometry(stumpRadius, stumpRadius, stumpHeight, 16);
            const stump = new THREE.Mesh(stumpGeo, stumpMat);
            stump.position.x = i * spacing;
            stumpsGroup.add(stump);
        }

        // 2 Bails resting on top
        const bailGeo = new THREE.CylinderGeometry(0.035, 0.035, 0.42, 8);
        const bailMat = new THREE.MeshStandardMaterial({ color: 0xd2a679, roughness: 0.4 });

        const bail1 = new THREE.Mesh(bailGeo, bailMat);
        bail1.position.set(-spacing / 2, stumpHeight / 2 + 0.05, 0);
        bail1.rotation.z = Math.PI / 2;
        stumpsGroup.add(bail1);

        const bail2 = new THREE.Mesh(bailGeo, bailMat);
        bail2.position.set(spacing / 2, stumpHeight / 2 + 0.05, 0);
        bail2.rotation.z = Math.PI / 2;
        stumpsGroup.add(bail2);

        // Position floating on the left side of background
        stumpsGroup.position.set(-5.5, -0.8, -2.5);
        stumpsGroup.rotation.y = 0.4;
        stumpsGroup.rotation.z = -0.15;
        scene.add(stumpsGroup);
    }

    function onWindowResize() {
        if (!camera || !renderer) return;
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }

    function animate() {
        requestAnimationFrame(animate);

        const elapsedTime = clock.getElapsedTime();

        // Ball continuous slow rotation + mouse tilt parallax
        if (ballMesh) {
            ballMesh.rotation.y += 0.008;
            ballMesh.rotation.x += 0.004;

            // Smooth parallax tilt towards mouse
            targetRotationY = mouseX * 0.75;
            targetRotationX = -mouseY * 0.6;
            ballMesh.rotation.z += (targetRotationY - ballMesh.rotation.z) * 0.05;
            ballMesh.rotation.x += (targetRotationX - ballMesh.rotation.x) * 0.05;

            // Subtle breathing floating motion
            ballMesh.position.y = 0.2 + Math.sin(elapsedTime * 1.5) * 0.12;
        }

        // Floating Bat animation
        if (batGroup) {
            batGroup.position.y = -0.5 + Math.sin(elapsedTime * 1.2 + 1) * 0.25;
            batGroup.rotation.y = -0.4 + Math.sin(elapsedTime * 0.8) * 0.15;
            batGroup.rotation.z = 0.35 + (mouseX * 0.1);
        }

        // Floating Stumps animation
        if (stumpsGroup) {
            stumpsGroup.position.y = -0.8 + Math.cos(elapsedTime * 1.1) * 0.2;
            stumpsGroup.rotation.y = 0.4 + Math.cos(elapsedTime * 0.7) * 0.12;
            stumpsGroup.rotation.z = -0.15 + (-mouseY * 0.08);
        }

        renderer.render(scene, camera);
    }

    function initCssFallback() {
        if (!container) return;
        container.innerHTML = `
            <div class="css-ball-wrapper" id="css-ball-wrapper">
                <div class="css-cricket-ball" id="css-cricket-ball">
                    <div class="css-seam"></div>
                    <div class="css-ball-shine"></div>
                    <div class="css-ball-text">CRICBRAIN</div>
                </div>
            </div>
            <div class="css-floating-bat" id="css-floating-bat">🏏</div>
            <div class="css-floating-stumps" id="css-floating-stumps">
                <span class="stump"></span>
                <span class="stump"></span>
                <span class="stump"></span>
            </div>
        `;

        const ball = document.getElementById("css-cricket-ball");
        if (ball && !prefersReducedMotion) {
            window.addEventListener("mousemove", (e) => {
                const x = (e.clientX / window.innerWidth - 0.5) * 40;
                const y = (e.clientY / window.innerHeight - 0.5) * -40;
                ball.style.transform = `rotateY(${x}deg) rotateX(${y}deg)`;
            });
        }
    }
})();
