/**
 * RecycleMe Master All-in-One Platform Controller
 * Handles:
 * 1. Shared UI animations, tooltips, cursor effects, and Scrollspy
 * 2. Feature 1: AI Waste Detection & Upcycling Studio (Upload/Camera + "What Can Be Made?")
 * 3. Feature 2: Smart Reverse Vending Machine (RVM) Interactive Kiosk Simulator
 * 4. Feature 3: Rewards Store 1-Click Voucher Redemption
 * 5. Feature 4: Real-time Live Webcam Stream & HUD Overlay
 * 6. Feature 6: Interactive Campus Smart Bins Leaflet Map & Geolocation
 */

(function () {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isFinePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  // ---------- Utility Helpers ----------
  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function setPointerMagnet(el, event) {
    const rect = el.getBoundingClientRect();
    const dx = event.clientX - (rect.left + rect.width / 2);
    const dy = event.clientY - (rect.top + rect.height / 2);
    el.style.setProperty("--mag-x", `${dx}px`);
    el.style.setProperty("--mag-y", `${dy}px`);
  }

  // Soft glow on buttons
  qsa(".btn, .btn-master-detect, .item-btn, .jump-pill").forEach((btn) => {
    btn.addEventListener("pointermove", (e) => {
      const rect = btn.getBoundingClientRect();
      btn.style.setProperty("--x", `${e.clientX - rect.left}px`);
      btn.style.setProperty("--y", `${e.clientY - rect.top}px`);
      setPointerMagnet(btn, e);
    });
    btn.addEventListener("pointerleave", () => {
      btn.style.removeProperty("--mag-x");
      btn.style.removeProperty("--mag-y");
    });
  });

  // Auto-dismiss flash alerts
  qsa("[data-auto-dismiss]").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.35s ease, transform 0.35s ease";
      el.style.opacity = "0";
      el.style.transform = "translateY(-6px)";
      setTimeout(() => el.remove(), 380);
    }, 4200);
  });

  // Cursor glow trail
  const cursorGlow = qs("#cursor-glow");
  if (cursorGlow && isFinePointer && !reduceMotion) {
    document.body.classList.add("has-pointer");
    let gx = window.innerWidth / 2, gy = window.innerHeight / 2;
    let tx = gx, ty = gy;
    document.addEventListener("pointermove", (e) => {
      tx = e.clientX;
      ty = e.clientY;
    });
    function drawGlow() {
      gx += (tx - gx) * 0.12;
      gy += (ty - gy) * 0.12;
      cursorGlow.style.left = `${gx}px`;
      cursorGlow.style.top = `${gy}px`;
      requestAnimationFrame(drawGlow);
    }
    requestAnimationFrame(drawGlow);
  }

  // Ambient particles
  const particleCanvas = qs("#particle-canvas");
  if (particleCanvas && !reduceMotion) {
    const ctx = particleCanvas.getContext("2d", { alpha: true });
    let dots = [];
    let w = 0, h = 0;
    function resizeCanvas() {
      w = window.innerWidth;
      h = window.innerHeight;
      particleCanvas.width = w;
      particleCanvas.height = h;
      dots = [];
      const count = w < 700 ? 10 : 20;
      for (let i = 0; i < count; i++) {
        dots.push({
          x: Math.random() * w,
          y: Math.random() * h,
          r: Math.random() * 1.8 + 0.8,
          vx: (Math.random() - 0.5) * 0.18,
          vy: (Math.random() - 0.5) * 0.18,
          a: Math.random() * 0.25 + 0.1,
        });
      }
    }
    function renderParticles() {
      ctx.clearRect(0, 0, w, h);
      dots.forEach((d) => {
        d.x += d.vx;
        d.y += d.vy;
        if (d.x < -10 || d.x > w + 10) d.vx *= -1;
        if (d.y < -10 || d.y > h + 10) d.vy *= -1;
        ctx.beginPath();
        ctx.fillStyle = `rgba(16, 185, 129, ${d.a})`;
        ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
        ctx.fill();
      });
      requestAnimationFrame(renderParticles);
    }
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    requestAnimationFrame(renderParticles);
  }

  // Scrollspy: Highlight active link in Navbar and Hero Jump bar
  const navSections = qsa("section.landing-section[id]");
  const navLinks = qsa(".nav-links a[href^='#']");
  const heroPills = qsa(".hero-jump-bar a[href^='#']");

  function onScrollSpy() {
    const scrollPos = window.scrollY + 140;
    let currentId = "";

    navSections.forEach((sec) => {
      const top = sec.offsetTop;
      const height = sec.offsetHeight;
      if (scrollPos >= top && scrollPos < top + height) {
        currentId = sec.getAttribute("id");
      }
    });

    if (!currentId && navSections.length) {
      currentId = navSections[0].getAttribute("id");
    }

    if (currentId) {
      navLinks.forEach((link) => {
        const href = link.getAttribute("href");
        if (href === `#${currentId}`) {
          link.classList.add("active");
        } else {
          link.classList.remove("active");
        }
      });
      heroPills.forEach((pill) => {
        const href = pill.getAttribute("href");
        if (href === `#${currentId}`) {
          pill.classList.add("active");
        } else {
          pill.classList.remove("active");
        }
      });
    }
  }
  window.addEventListener("scroll", onScrollSpy, { passive: true });
  onScrollSpy();

  // =========================================================================
  // FEATURE 1: AI WASTE DETECTION & UPCYCLING STUDIO
  // =========================================================================
  const tabUpload = qs("#tab-btn-upload");
  const tabCamera = qs("#tab-btn-camera");
  const paneUpload = qs("#pane-upload");
  const paneCamera = qs("#pane-camera");
  const dropzone = qs("#studio-dropzone");
  const fileInput = qs("#file-input");
  const dropDefaultView = qs("#drop-default-view");
  const previewWrap = qs("#upload-preview-wrap");
  const previewImg = qs("#upload-preview-img");
  const btnMasterDetect = qs("#btn-master-detect");
  const btnClearChoice = qs("#btn-clear-choice");

  const camVideo = qs("#studio-cam-video");
  const camOverlay = qs("#studio-cam-overlay");
  const camPlaceholder = qs("#studio-cam-placeholder");
  const camScanLine = qs("#cam-scan-line");
  const btnStartCam = qs("#btn-start-camera");
  const btnSnapCam = qs("#btn-snap-camera");
  const btnStopCam = qs("#btn-stop-camera");

  const resultsWorkspace = qs("#studio-results-workspace");
  const resAnnotatedImg = qs("#res-annotated-img");
  const resClassName = qs("#res-class-name");
  const resConfScore = qs("#res-conf-score");
  const resRecGuide = qs("#res-rec-guide");
  const resDisposalTips = qs("#res-disposal-tips");
  const resBinIcon = qs("#res-bin-icon");
  const resBinType = qs("#res-bin-type");
  const resBinLocation = qs("#res-bin-location");
  const upcyclingShowcase = qs("#upcycling-showcase");
  const upcyclingMaterialTag = qs("#upcycling-material-tag");
  const upcyclingGrid = qs("#upcycling-products-grid");

  let activeMode = "upload"; // "upload" | "camera"
  let selectedFile = null;
  let studioCamStream = null;
  let isStudioCamActive = false;

  const CLASS_COLORS = {
    plastic: "#0284c7",
    paper: "#059669",
    cardboard: "#d97706",
    glass: "#b45309",
    metal: "#7c3aed",
    organic: "#16a34a",
    other: "#dc2626",
    trash: "#64748b",
  };

  // Switch tabs
  if (tabUpload && tabCamera) {
    tabUpload.addEventListener("click", () => {
      activeMode = "upload";
      tabUpload.classList.add("active");
      tabCamera.classList.remove("active");
      tabUpload.setAttribute("aria-selected", "true");
      tabCamera.setAttribute("aria-selected", "false");
      if (paneUpload) paneUpload.classList.add("active");
      if (paneCamera) paneCamera.classList.remove("active");
      stopStudioCamera();
      updateDetectBtnState();
    });

    tabCamera.addEventListener("click", () => {
      activeMode = "camera";
      tabCamera.classList.add("active");
      tabUpload.classList.remove("active");
      tabCamera.setAttribute("aria-selected", "true");
      tabUpload.setAttribute("aria-selected", "false");
      if (paneCamera) paneCamera.classList.add("active");
      if (paneUpload) paneUpload.classList.remove("active");
      updateDetectBtnState();
    });
  }

  // File selection and drag-drop
  if (dropzone && fileInput) {
    dropzone.addEventListener("click", (e) => {
      if (e.target !== fileInput) fileInput.click();
    });

    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files[0]) {
        stageFile(fileInput.files[0]);
      }
    });

    ["dragenter", "dragover"].forEach((ev) => {
      dropzone.addEventListener(ev, (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((ev) => {
      dropzone.addEventListener(ev, (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
        const f = e.dataTransfer.files[0];
        const dt = new DataTransfer();
        dt.items.add(f);
        fileInput.files = dt.files;
        stageFile(f);
      }
    });
  }

  function stageFile(file) {
    if (!file || !file.type.startsWith("image/")) {
      alert("Please choose a valid image file (JPG, PNG, WEBP).");
      return;
    }
    selectedFile = file;
    const url = URL.createObjectURL(file);
    if (previewImg) previewImg.src = url;
    if (dropDefaultView) dropDefaultView.style.display = "none";
    if (previewWrap) previewWrap.style.display = "block";
    if (dropzone) dropzone.classList.add("has-file");
    updateDetectBtnState();
  }

  function resetStudioSelection() {
    selectedFile = null;
    if (fileInput) fileInput.value = "";
    if (previewImg) previewImg.src = "";
    if (dropDefaultView) dropDefaultView.style.display = "block";
    if (previewWrap) previewWrap.style.display = "none";
    if (dropzone) dropzone.classList.remove("has-file");
    if (resultsWorkspace) resultsWorkspace.style.display = "none";
    updateDetectBtnState();
  }

  if (btnClearChoice) {
    btnClearChoice.addEventListener("click", resetStudioSelection);
  }

  function updateDetectBtnState() {
    if (!btnMasterDetect) return;
    if (activeMode === "upload") {
      btnMasterDetect.disabled = !selectedFile;
    } else {
      btnMasterDetect.disabled = !isStudioCamActive;
    }
  }

  // Camera in Studio
  async function startStudioCamera() {
    try {
      const constraints = {
        video: { facingMode: { ideal: "environment" }, width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      };
      try {
        studioCamStream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (err) {
        studioCamStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }

      if (camVideo) {
        camVideo.srcObject = studioCamStream;
        camVideo.play();
      }
      if (camPlaceholder) camPlaceholder.style.display = "none";
      if (camScanLine) camScanLine.style.display = "block";
      isStudioCamActive = true;
      if (btnStartCam) btnStartCam.disabled = true;
      if (btnSnapCam) btnSnapCam.disabled = false;
      if (btnStopCam) btnStopCam.disabled = false;
      updateDetectBtnState();
    } catch (err) {
      alert("Camera access denied or unavailable: " + err.message);
    }
  }

  function stopStudioCamera() {
    if (studioCamStream) {
      studioCamStream.getTracks().forEach((t) => t.stop());
      studioCamStream = null;
    }
    if (camVideo) camVideo.srcObject = null;
    if (camPlaceholder) camPlaceholder.style.display = "block";
    if (camScanLine) camScanLine.style.display = "none";
    isStudioCamActive = false;
    if (btnStartCam) btnStartCam.disabled = false;
    if (btnSnapCam) btnSnapCam.disabled = true;
    if (btnStopCam) btnStopCam.disabled = true;
    updateDetectBtnState();
  }

  if (btnStartCam) btnStartCam.addEventListener("click", startStudioCamera);
  if (btnStopCam) btnStopCam.addEventListener("click", stopStudioCamera);

  function snapStudioCameraToBlob() {
    return new Promise((resolve) => {
      if (!camVideo || !camVideo.videoWidth) {
        resolve(null);
        return;
      }
      const canvas = document.createElement("canvas");
      canvas.width = camVideo.videoWidth;
      canvas.height = camVideo.videoHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(camVideo, 0, 0);
      canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.9);
    });
  }

  if (btnSnapCam) {
    btnSnapCam.addEventListener("click", async () => {
      await runDetectionWorkflow(true);
    });
  }

  if (btnMasterDetect) {
    btnMasterDetect.addEventListener("click", async () => {
      await runDetectionWorkflow(activeMode === "camera");
    });
  }

  async function runDetectionWorkflow(fromSnap) {
    let fileToUpload = selectedFile;
    if (fromSnap) {
      const blob = await snapStudioCameraToBlob();
      if (!blob) {
        alert("Please position waste item in camera view before scanning.");
        return;
      }
      fileToUpload = new File([blob], "camera_capture.jpg", { type: "image/jpeg" });
    }

    if (!fileToUpload) {
      alert("Please upload a photo or turn on camera first.");
      return;
    }

    const origHtml = btnMasterDetect.innerHTML;
    btnMasterDetect.disabled = true;
    btnMasterDetect.innerHTML = `<span>⏳</span> Analyzing waste neural features…`;

    const formData = new FormData();
    formData.append("image", fileToUpload);

    try {
      const resp = await fetch("/api/detect", {
        method: "POST",
        body: formData,
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      const data = await resp.json();
      if (!data.success) {
        throw new Error(data.error || "Neural detection failed.");
      }

      renderStudioResults(data);
    } catch (err) {
      alert("Detection error: " + err.message);
    } finally {
      btnMasterDetect.disabled = false;
      btnMasterDetect.innerHTML = origHtml;
    }
  }

  function renderStudioResults(data) {
    if (!resultsWorkspace) return;
    resultsWorkspace.style.display = "block";

    window.CURRENT_DETECTION_ID = data.detection_id;
    window.CURRENT_DEPOSIT_ITEMS = data.deposit_items || [];

    const imgPath = data.result_image ? `/static/${data.result_image}?t=${Date.now()}` : `/static/${data.upload_url}`;
    if (resAnnotatedImg) resAnnotatedImg.src = imgPath;

    const cls = (data.primary_class || "other").toLowerCase();
    const clsUpper = cls.toUpperCase();
    const confPct = data.primary_confidence ? (data.primary_confidence * 100).toFixed(1) : "95.0";
    const color = CLASS_COLORS[cls] || "#059669";

    if (resClassName) {
      resClassName.textContent = clsUpper;
      resClassName.style.color = color;
      resClassName.style.borderColor = color;
    }
    if (resConfScore) {
      resConfScore.textContent = `${confPct}% Conf.`;
      resConfScore.style.color = color;
    }
    if (resRecGuide) {
      resRecGuide.textContent = data.primary_recommendation || "Follow proper segregation rules for this item.";
    }

    const primaryDet = (data.detections && data.detections[0]) || {};
    if (resDisposalTips) {
      resDisposalTips.textContent = primaryDet.disposal_tips || "Rinse container, empty residual liquids, and place in clean recyclable stream.";
    }

    const binInfo = data.bin_info || {};
    if (resBinIcon) resBinIcon.textContent = binInfo.icon || "🗑️";
    if (resBinType) resBinType.textContent = binInfo.bin_type || `${clsUpper} Bin`;
    if (resBinLocation) resBinLocation.textContent = binInfo.location || "Campus Center Station";

    // Render "What Can Be Made From This?" Showcase
    renderUpcyclingShowcase(cls, data.what_can_be_made || primaryDet.what_can_be_made);

    // Update campus map marker & focus
    if (window.focusMapStation) {
      window.focusMapStation(cls);
    }

    resultsWorkspace.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderUpcyclingShowcase(wasteClass, products) {
    if (upcyclingMaterialTag) {
      upcyclingMaterialTag.textContent = `What Can Be Made From Recycled ${wasteClass.toUpperCase()}?`;
    }
    if (!upcyclingGrid) return;
    upcyclingGrid.innerHTML = "";

    if (!products || !products.length) {
      upcyclingGrid.innerHTML = `
        <div style="grid-column: 1/-1; text-align:center; padding:20px; color:#64748b;">
          Recycling and transformation items loaded for ${wasteClass}.
        </div>
      `;
      return;
    }

    products.forEach((p) => {
      const card = document.createElement("div");
      card.className = "upcycling-item-card";
      card.innerHTML = `
        <div class="upcycling-item-top">
          <div class="upcycling-icon-box">${p.icon || "♻️"}</div>
          <span class="upcycling-badge">${p.badge || "Upcycled"}</span>
        </div>
        <h4 class="upcycling-title">${p.title || "Repurposed Product"}</h4>
        <p class="upcycling-desc">${p.description || "Manufactured from segregated post-consumer recyclables into high utility goods."}</p>
      `;
      upcyclingGrid.appendChild(card);
    });
  }

  // =========================================================================
  // FEATURE 2: SMART REVERSE VENDING MACHINE (RVM) KIOSK CONTROLLER
  // =========================================================================
  let kioskItems = [];

  window.addKioskItem = function (category, name, icon, points, weight) {
    kioskItems.push({
      class_name: category,
      display_name: name,
      icon: icon || "♻️",
      points: points || 15,
      weight_kg: weight || 0.05,
      quantity: 1,
    });

    // Animate hatch door
    const door = qs("#kiosk-hatch-door");
    if (door) {
      door.style.transform = "scaleY(0.15)";
      setTimeout(() => {
        door.style.transform = "scaleY(1)";
      }, 350);
    }

    renderKioskLedger();
  };

  window.removeKioskItem = function (index) {
    kioskItems.splice(index, 1);
    renderKioskLedger();
  };

  function renderKioskLedger() {
    const list = qs("#kiosk-items-list");
    const emptyMsg = qs("#kiosk-empty-msg");
    const countEl = qs("#kiosk-items-count");
    const weightEl = qs("#kiosk-total-weight");
    const ptsEl = qs("#kiosk-total-points");
    const btnDeposit = qs("#btn-kiosk-deposit");

    if (!list) return;

    if (kioskItems.length === 0) {
      list.innerHTML = `
        <div style="text-align:center; padding:30px 10px; color:#94a3b8; font-size:0.9rem;" id="kiosk-empty-msg">
          No items inserted into chamber yet.<br/>Click items on the left to feed this smart machine!
        </div>
      `;
      if (countEl) countEl.textContent = "0 items";
      if (weightEl) weightEl.textContent = "0.00 kg";
      if (ptsEl) ptsEl.textContent = "+0 pts";
      if (btnDeposit) btnDeposit.disabled = true;
      return;
    }

    let totalWeight = 0;
    let totalPts = 0;
    list.innerHTML = "";

    kioskItems.forEach((it, idx) => {
      totalWeight += it.weight_kg;
      totalPts += it.points;

      const row = document.createElement("div");
      row.className = "session-item-row";
      row.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="font-size:1.3rem;">${it.icon}</span>
          <div>
            <div style="font-weight:700; color:#0f172a; font-size:0.88rem;">${it.display_name}</div>
            <div style="font-size:0.75rem; color:#64748b;">${it.weight_kg.toFixed(2)} kg · +${it.points} pts</div>
          </div>
        </div>
        <button type="button" class="btn-item-del" onclick="removeKioskItem(${idx})" title="Eject item">✕</button>
      `;
      list.appendChild(row);
    });

    if (countEl) countEl.textContent = `${kioskItems.length} item${kioskItems.length > 1 ? "s" : ""}`;
    if (weightEl) weightEl.textContent = `${totalWeight.toFixed(2)} kg`;
    if (ptsEl) ptsEl.textContent = `+${totalPts} pts`;
    if (btnDeposit) btnDeposit.disabled = false;
  }

  window.executeKioskDeposit = async function () {
    const btnDeposit = qs("#btn-kiosk-deposit");
    const machineSelect = qs("#kiosk-machine-selector");
    const machineId = machineSelect ? machineSelect.value : "RVM-01-CAMPUS-NORTH";

    if (!kioskItems.length) {
      alert("Please insert at least one item into the chamber.");
      return;
    }

    if (btnDeposit) {
      btnDeposit.disabled = true;
      btnDeposit.innerHTML = `<span>⏳</span> Depositing in RVM…`;
    }

    try {
      const resp = await fetch("/api/disposal/deposit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          machine_id: machineId,
          items: kioskItems,
          detection_id: window.CURRENT_DETECTION_ID || null,
        }),
      });

      const res = await resp.json();
      if (!res.success) {
        throw new Error(res.error || "Deposit transaction could not be completed.");
      }

      // Confetti celebration!
      if (typeof confetti === "function") {
        confetti({
          particleCount: 120,
          spread: 80,
          origin: { y: 0.6 },
          colors: ["#10b981", "#0284c7", "#fbbf24", "#a855f7"],
        });
      }

      // Update Points badges
      const userPtsBadge = qs(".user-points-badge span:nth-child(2)");
      if (userPtsBadge && res.new_balance !== undefined) {
        userPtsBadge.textContent = `${res.new_balance} pts`;
      }
      const heroPts = qs("#hero-user-points");
      if (heroPts && res.new_balance !== undefined) {
        heroPts.textContent = `⭐ ${res.new_balance}`;
      }

      alert(`🎉 Deposit Successful!\n\nYou earned +${res.points_earned} points!\nNew Balance: ${res.new_balance} pts\nReceipt Token: ${res.receipt_token}`);

      kioskItems = [];
      renderKioskLedger();
    } catch (err) {
      alert("Deposit Error: " + err.message);
    } finally {
      if (btnDeposit) {
        btnDeposit.disabled = kioskItems.length === 0;
        btnDeposit.innerHTML = `<span>🎁</span> Complete Deposit &amp; Claim Points`;
      }
    }
  };

  // =========================================================================
  // FEATURE 3: USER REWARDS & VOUCHER STORE CONTROLLER
  // =========================================================================
  window.redeemRewardItem = async function (rewardId, title, pointsCost) {
    const confirmMsg = `Redeem voucher:\n"${title}"\nCost: ${pointsCost} reward points\n\nWould you like to proceed?`;
    if (!confirm(confirmMsg)) return;

    try {
      const resp = await fetch("/api/rewards/redeem", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reward_id: rewardId }),
      });

      const data = await resp.json();
      if (!data.success) {
        throw new Error(data.error || "Could not redeem reward.");
      }

      if (typeof confetti === "function") {
        confetti({
          particleCount: 90,
          spread: 70,
          origin: { y: 0.5 },
          colors: ["#fbbf24", "#10b981", "#0284c7"],
        });
      }

      // Update Points badges
      const userPtsBadge = qs(".user-points-badge span:nth-child(2)");
      if (userPtsBadge && data.new_balance !== undefined) {
        userPtsBadge.textContent = `${data.new_balance} pts`;
      }
      const heroPts = qs("#hero-user-points");
      if (heroPts && data.new_balance !== undefined) {
        heroPts.textContent = `⭐ ${data.new_balance}`;
      }

      alert(`🎟️ Voucher Redeemed Successfully!\n\nReward: ${title}\nVoucher Code: ${data.voucher_code}\nRemaining Balance: ${data.new_balance} pts\n\nShow this voucher code at campus counter!`);
    } catch (err) {
      alert("Redemption notice: " + err.message);
    }
  };

  // =========================================================================
  // FEATURE 4: REAL-TIME LIVE WEBCAM SCANNER CONTROLLER
  // =========================================================================
  const liveVideo = qs("#realtime-video");
  const liveCanvas = qs("#realtime-overlay");
  const livePlaceholder = qs("#realtime-placeholder");
  const liveClassEl = qs("#live-detected-class");
  const liveConfEl = qs("#live-detected-conf");
  const liveAdviceEl = qs("#live-bin-advice");
  const btnLiveStart = qs("#btn-realtime-start");
  const btnLiveStop = qs("#btn-realtime-stop");

  let liveStream = null;
  let liveTimer = null;
  let isLiveStreaming = false;

  window.startRealtimeStream = async function () {
    try {
      const constraints = {
        video: { facingMode: { ideal: "environment" }, width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      };
      try {
        liveStream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (err) {
        liveStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }

      if (liveVideo) {
        liveVideo.srcObject = liveStream;
        liveVideo.play();
      }
      if (livePlaceholder) livePlaceholder.style.display = "none";
      if (btnLiveStart) btnLiveStart.disabled = true;
      if (btnLiveStop) btnLiveStop.disabled = false;
      isLiveStreaming = true;

      // Periodic frame analysis
      liveTimer = setInterval(analyzeLiveStreamFrame, 1300);
    } catch (err) {
      alert("Could not access live camera: " + err.message);
    }
  };

  window.stopRealtimeStream = function () {
    if (liveStream) {
      liveStream.getTracks().forEach((t) => t.stop());
      liveStream = null;
    }
    if (liveVideo) liveVideo.srcObject = null;
    if (liveTimer) {
      clearInterval(liveTimer);
      liveTimer = null;
    }
    if (liveCanvas) {
      const ctx = liveCanvas.getContext("2d");
      ctx.clearRect(0, 0, liveCanvas.width, liveCanvas.height);
    }
    if (livePlaceholder) livePlaceholder.style.display = "block";
    if (btnLiveStart) btnLiveStart.disabled = false;
    if (btnLiveStop) btnLiveStop.disabled = true;
    if (liveClassEl) liveClassEl.textContent = "—";
    if (liveConfEl) liveConfEl.textContent = "Camera feed stopped";
    if (liveAdviceEl) liveAdviceEl.textContent = "Click 'Start Real-Time Camera' above";
    isLiveStreaming = false;
  };

  async function analyzeLiveStreamFrame() {
    if (!isLiveStreaming || !liveVideo || !liveVideo.videoWidth) return;

    const offscreen = document.createElement("canvas");
    offscreen.width = liveVideo.videoWidth;
    offscreen.height = liveVideo.videoHeight;
    const offCtx = offscreen.getContext("2d");
    offCtx.drawImage(liveVideo, 0, 0);

    const b64Data = offscreen.toDataURL("image/jpeg", 0.7);

    try {
      const resp = await fetch("/api/live_detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_data: b64Data }),
      });

      const res = await resp.json();
      if (!res.success) return;

      drawLiveBoundingBoxes(res);
    } catch (err) {
      // Ignore transient network errors during live streaming
    }
  }

  function drawLiveBoundingBoxes(res) {
    if (!liveCanvas || !liveVideo) return;
    liveCanvas.width = liveVideo.videoWidth || 640;
    liveCanvas.height = liveVideo.videoHeight || 480;
    const ctx = liveCanvas.getContext("2d");
    ctx.clearRect(0, 0, liveCanvas.width, liveCanvas.height);

    const detections = res.detections || [];
    if (!detections.length) {
      if (liveClassEl) liveClassEl.textContent = "Searching for waste…";
      if (liveConfEl) liveConfEl.textContent = "Hold bottle, can, or box in view";
      return;
    }

    const top = detections[0];
    const cls = (top.class_name || "waste").toUpperCase();
    const conf = top.confidence ? (top.confidence * 100).toFixed(1) : "92";

    if (liveClassEl) liveClassEl.textContent = cls;
    if (liveConfEl) liveConfEl.textContent = `${conf}% Confidence`;
    if (liveAdviceEl) liveAdviceEl.textContent = res.recommendation || "Sort into designated campus bin";

    detections.forEach((det) => {
      const box = det.box;
      if (!box) return;
      const x1 = box[0], y1 = box[1], x2 = box[2], y2 = box[3];
      const w = x2 - x1, h = y2 - y1;

      ctx.strokeStyle = "#10b981";
      ctx.lineWidth = 3;
      ctx.strokeRect(x1, y1, w, h);

      ctx.fillStyle = "rgba(16, 185, 129, 0.85)";
      ctx.fillRect(x1, Math.max(0, y1 - 24), Math.max(120, w), 24);

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 13px sans-serif";
      ctx.fillText(`${det.class_name.toUpperCase()} ${(det.confidence * 100).toFixed(0)}%`, x1 + 6, Math.max(16, y1 - 7));
    });
  }

  // =========================================================================
  // FEATURE 6: CAMPUS SMART BINS INTERACTIVE LEAFLET MAP
  // =========================================================================
  let campusMasterMap = null;
  let campusMarkers = {};

  function initCampusMasterMap() {
    const mapEl = qs("#campus-master-map");
    if (!mapEl || typeof L === "undefined") return;

    const data = window.SERVER_MAP_DATA || {};
    const center = data.center || { lat: 12.9716, lng: 77.5946, zoom: 17 };
    const bins = data.bins || {};

    if (!campusMasterMap) {
      campusMasterMap = L.map("campus-master-map", { scrollWheelZoom: false }).setView([center.lat, center.lng], center.zoom || 17);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
        maxZoom: 19,
      }).addTo(campusMasterMap);

      Object.keys(bins).forEach((key) => {
        const b = bins[key];
        if (b.lat && b.lng) {
          const marker = L.marker([b.lat, b.lng]).addTo(campusMasterMap);
          marker.bindPopup(`
            <div style="font-family:sans-serif; min-width:200px;">
              <strong style="color:#059669; font-size:14px;">${b.icon || "🗑️"} ${b.bin_type || key.toUpperCase()}</strong>
              <div style="font-size:12px; color:#475569; margin-top:3px;">${b.facility_name || ""}</div>
              <div style="font-size:11px; color:#64748b;">${b.location || ""}</div>
              <div style="font-size:11px; color:#10b981; font-weight:bold; margin-top:4px;">⏱️ ${b.operating_hours || "24/7 Open"}</div>
            </div>
          `);
          campusMarkers[key] = { marker, data: b };
        }
      });
    }
  }

  window.focusMapStation = function (binKey) {
    if (!campusMasterMap && typeof L !== "undefined") {
      initCampusMasterMap();
    }
    if (!campusMasterMap) return;

    const item = campusMarkers[binKey];
    if (item && item.data && item.data.lat && item.data.lng) {
      campusMasterMap.setView([item.data.lat, item.data.lng], 18);
      item.marker.openPopup();
    }
  };

  window.filterMapMarkers = function (category) {
    if (!campusMasterMap) initCampusMasterMap();
    if (!campusMasterMap) return;

    qsa("#map-filter-buttons button").forEach((b) => {
      b.classList.toggle("active", b.textContent.toLowerCase().includes(category));
    });

    Object.keys(campusMarkers).forEach((k) => {
      const obj = campusMarkers[k];
      if (category === "all" || k === category) {
        obj.marker.addTo(campusMasterMap);
      } else {
        campusMasterMap.removeLayer(obj.marker);
      }
    });
  };

  window.locateUserGPS = function () {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (!campusMasterMap) initCampusMasterMap();
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        if (campusMasterMap) {
          campusMasterMap.setView([lat, lng], 17);
          const userMarker = L.circleMarker([lat, lng], {
            radius: 8,
            fillColor: "#0284c7",
            color: "#ffffff",
            weight: 3,
            opacity: 1,
            fillOpacity: 0.9,
          }).addTo(campusMasterMap);
          userMarker.bindPopup("<strong>📍 You Are Here</strong><br>Locating nearest recycling bins…").openPopup();
        }
      },
      (err) => {
        alert("GPS location notice: " + err.message);
      },
      { timeout: 8000 }
    );
  };

  // Auto-init on page load
  window.addEventListener("load", () => {
    initCampusMasterMap();
  });

  window.addEventListener("beforeunload", () => {
    stopStudioCamera();
    window.stopRealtimeStream();
  });
})();
