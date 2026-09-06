/**
 * Interactive WasteSort UI:
 * drag-drop upload, camera capture, loading overlay,
 * pipeline steps, confidence bar animation, button glow.
 */
(function () {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isFinePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  // ---------- Shared UI helpers ----------
  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function clamp(v, min, max) {
    return Math.min(max, Math.max(min, v));
  }

  function setPointerMagnet(el, event) {
    const rect = el.getBoundingClientRect();
    const dx = event.clientX - (rect.left + rect.width / 2);
    const dy = event.clientY - (rect.top + rect.height / 2);
    el.style.setProperty("--mag-x", `${dx}px`);
    el.style.setProperty("--mag-y", `${dy}px`);
  }

  // Soft glow follows cursor on primary/secondary buttons
  qsa(".btn").forEach((btn) => {
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

  // Auto-dismiss flash messages
  qsa("[data-auto-dismiss]").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.35s ease, transform 0.35s ease";
      el.style.opacity = "0";
      el.style.transform = "translateY(-6px)";
      setTimeout(() => el.remove(), 380);
    }, 4200);
  });

  // Animate confidence bars + counters on result page
  function animateConfidence() {
    qsa(".conf-fill").forEach((bar) => {
      const width = parseFloat(bar.getAttribute("data-width") || "0");
      requestAnimationFrame(() => {
        bar.style.width = `${Math.max(0, Math.min(100, width))}%`;
      });
    });

    qsa(".conf-value[data-target]").forEach((el) => {
      const target = parseFloat(el.getAttribute("data-target") || "0");
      if (reduceMotion) {
        el.textContent = `${target.toFixed(1)}%`;
        return;
      }
      const duration = 900;
      const start = performance.now();
      function tick(now) {
        const t = Math.min(1, (now - start) / duration);
        const eased = 1 - Math.pow(1 - t, 3);
        el.textContent = `${(target * eased).toFixed(1)}%`;
        if (t < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }
  animateConfidence();

  const revealTargets = qsa(".reveal, .stagger");
  if (revealTargets.length) {
    if (reduceMotion || !("IntersectionObserver" in window)) {
      revealTargets.forEach((el) => el.classList.add("is-visible"));
    } else {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      }, { threshold: 0.14, rootMargin: "0px 0px -8% 0px" });
      revealTargets.forEach((el) => observer.observe(el));
    }
  }

  requestAnimationFrame(() => {
    document.body.classList.add("is-ready");
  });

  // Cursor glow trail for desktop pointers only
  const cursorGlow = qs("#cursor-glow");
  if (cursorGlow && isFinePointer && !reduceMotion) {
    document.body.classList.add("has-pointer");
    let gx = window.innerWidth / 2;
    let gy = window.innerHeight / 2;
    let tx = gx;
    let ty = gy;
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

  // Lightweight ambient particles
  const particleCanvas = qs("#particle-canvas");
  if (particleCanvas && !reduceMotion) {
    const ctx = particleCanvas.getContext("2d", { alpha: true });
    const dots = [];
    let w = 0;
    let h = 0;
    let dotCount = 24;

    function resizeCanvas() {
      w = window.innerWidth;
      h = window.innerHeight;
      particleCanvas.width = w;
      particleCanvas.height = h;
      dotCount = w < 700 ? 12 : 24;
      dots.length = 0;
      for (let i = 0; i < dotCount; i += 1) {
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
        ctx.fillStyle = `rgba(31, 122, 76, ${d.a})`;
        ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
        ctx.fill();
      });
      requestAnimationFrame(renderParticles);
    }

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    requestAnimationFrame(renderParticles);
  }

  // Chip helper text
  const chipTip = qs("#chip-tip");
  if (chipTip) {
    qsa(".chip[data-tip]").forEach((chip) => {
      chip.addEventListener("mouseenter", () => {
        chipTip.textContent = chip.getAttribute("data-tip") || "";
      });
      chip.addEventListener("focus", () => {
        chipTip.textContent = chip.getAttribute("data-tip") || "";
      });
      chip.addEventListener("mouseleave", () => {
        chipTip.textContent = "Hover a category to learn what it covers.";
      });
      chip.addEventListener("blur", () => {
        chipTip.textContent = "Hover a category to learn what it covers.";
      });
    });
  }

  // Animate hero flow indicator
  const flowItems = qsa(".flow-item");
  if (flowItems.length && !reduceMotion) {
    let idx = 0;
    setInterval(() => {
      flowItems.forEach((it, i) => it.classList.toggle("active", i === idx));
      idx = (idx + 1) % flowItems.length;
    }, 1300);
  }

  const interactiveCards = qsa(".tilt-card, .tilt-soft, .magnetic");
  interactiveCards.forEach((card) => {
    card.addEventListener("pointermove", (e) => setPointerMagnet(card, e));
    card.addEventListener("pointerleave", () => {
      card.style.removeProperty("--mag-x");
      card.style.removeProperty("--mag-y");
    });
  });

  // Loading overlay helpers
  const overlay = qs("#loading-overlay");
  const loaderSteps = qsa(".loader-step", overlay || document);

  function setLoaderStep(index) {
    loaderSteps.forEach((step, i) => {
      step.classList.toggle("active", i === index);
    });
  }

  function showLoading() {
    if (!overlay) return;
    overlay.hidden = false;
    setLoaderStep(0);
    if (!reduceMotion) {
      setTimeout(() => setLoaderStep(1), 500);
      setTimeout(() => setLoaderStep(2), 1100);
    } else {
      setLoaderStep(2);
    }
  }

  // ---------- Detect page ----------
  const form = qs("#detect-form");
  if (!form) return;

  const input = qs("#image-input");
  const preview = qs("#preview");
  const hint = qs("#preview-hint");
  const captureBtn = qs("#capture-btn");
  const browseBtn = qs("#browse-btn");
  const detectBtn = qs("#detect-btn");
  const video = qs("#camera");
  const canvas = qs("#capture-canvas");
  const dropzone = qs("#dropzone");
  const badge = qs("#preview-badge");
  const pipeSteps = qsa(".pipe-step");

  let stream = null;
  let capturing = false;

  function setPipeline(step) {
    pipeSteps.forEach((el) => {
      const n = clamp(Number(el.getAttribute("data-step")), 1, 3);
      el.classList.toggle("active", n === step);
      el.classList.toggle("done", n < step);
    });
  }

  function enableDetect(enabled) {
    if (detectBtn) detectBtn.disabled = !enabled;
  }

  function showPreview(url, label) {
    if (!preview) return;
    preview.src = url;
    preview.hidden = false;
    if (hint) hint.textContent = "Image ready. Click Detect Waste.";
    if (video) video.hidden = true;
    if (dropzone) {
      dropzone.classList.add("has-image");
      dropzone.classList.remove("camera-on", "dragover");
    }
    if (badge) {
      badge.hidden = false;
      badge.textContent = label || "Ready";
    }
    enableDetect(true);
    setPipeline(2);
  }

  function clearPreviewUi() {
    if (preview) {
      preview.hidden = true;
      preview.removeAttribute("src");
    }
    if (badge) badge.hidden = true;
    if (dropzone) dropzone.classList.remove("has-image");
  }

  function assignFile(file) {
    if (!file || !input) return;
    if (!file.type.startsWith("image/")) {
      if (hint) hint.textContent = "Please choose an image file.";
      return;
    }
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
    showPreview(URL.createObjectURL(file), file.name.split(".").pop().toUpperCase());
    stopCamera();
    capturing = false;
    if (captureBtn) captureBtn.textContent = "Capture Image";
  }

  if (browseBtn && input) {
    browseBtn.addEventListener("click", () => input.click());
  }

  if (input) {
    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      if (!file) return;
      showPreview(URL.createObjectURL(file), "Uploaded");
      stopCamera();
      capturing = false;
      if (captureBtn) captureBtn.textContent = "Capture Image";
    });
  }

  // Drag and drop
  if (dropzone) {
    ["dragenter", "dragover"].forEach((evt) => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add("dragover");
      });
    });
    ["dragleave", "drop"].forEach((evt) => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("dragover");
      });
    });
    dropzone.addEventListener("drop", (e) => {
      const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (file) assignFile(file);
    });
    dropzone.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        if (input) input.click();
      }
    });
  }

  async function startCamera() {
    if (!video) return;
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" },
      audio: false,
    });
    video.srcObject = stream;
    video.hidden = false;
    if (preview) preview.hidden = true;
    if (dropzone) {
      dropzone.classList.add("camera-on");
      dropzone.classList.remove("has-image");
    }
    if (badge) {
      badge.hidden = false;
      badge.textContent = "Live";
    }
    if (hint) hint.textContent = "Camera on — click Take Photo.";
    setPipeline(1);
  }

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      stream = null;
    }
    if (video) {
      video.srcObject = null;
      video.hidden = true;
    }
    if (dropzone) dropzone.classList.remove("camera-on");
  }

  function snapToFile() {
    if (!video || !canvas || !input) return;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);
    if (dropzone) {
      dropzone.classList.remove("flash-snap");
      void dropzone.offsetWidth;
      dropzone.classList.add("flash-snap");
    }
    canvas.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
      assignFile(file);
      if (badge) badge.textContent = "Captured";
    }, "image/jpeg", 0.92);
  }

  if (captureBtn) {
    captureBtn.addEventListener("click", async () => {
      try {
        if (!capturing) {
          await startCamera();
          capturing = true;
          captureBtn.textContent = "Take Photo";
        } else {
          snapToFile();
          capturing = false;
          captureBtn.textContent = "Capture Image";
        }
      } catch (err) {
        alert("Camera not available. Use Upload Image instead.\n" + err.message);
      }
    });
  }

  form.addEventListener("submit", (e) => {
    if (!input || !input.files || !input.files.length) {
      e.preventDefault();
      if (hint) hint.textContent = "Please upload or capture an image first.";
      if (dropzone) {
        dropzone.classList.remove("dragover");
        dropzone.animate(
          [
            { transform: "translateX(0)" },
            { transform: "translateX(-6px)" },
            { transform: "translateX(6px)" },
            { transform: "translateX(0)" },
          ],
          { duration: 360 }
        );
      }
      return;
    }
    setPipeline(3);
    if (detectBtn) detectBtn.classList.add("loading");
    showLoading();
  });

  setPipeline(1);
  window.addEventListener("beforeunload", stopCamera);
})();
