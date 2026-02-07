<script>
  import { onMount } from 'svelte';

  let canvasEl = $state(null);

  const attributes = [
    { label: 'Clarity', value: 9.2 },
    { label: 'Structure', value: 8.5 },
    { label: 'Power (Scale)', value: 6.8 },
    { label: 'Wisdom', value: 7.5 },
  ];

  const radarLabels = ['Clarity', 'Structure', 'Power', 'Wisdom', 'Speed', 'Security'];
  const radarValues = [9.2, 8.5, 6.8, 7.5, 8.0, 7.2];

  const strengths = [
    'Exceptional database schema design, showcasing deep understanding of relational magic.',
    'Strong communication skills; articulated trade-offs with wisdom.',
  ];

  const weaknesses = [
    'Neglected caching strategies for the read-heavy components.',
    'Initial load balancer configuration was too simplistic for high traffic spells.',
  ];

  const improvements = [
    { title: 'Master Distributed Caching', desc: 'Implement Redis or Memcached patterns to reduce database load during peak mana usage.' },
    { title: 'Study Async Processing', desc: 'Decouple heavy computation spells using message queues like Kafka.' },
    { title: 'Refine Sharding Techniques', desc: 'Learn horizontal partitioning to manage massive data volumes effectively.' },
  ];

  const rubric = [
    { label: 'Requirements Gathering', status: 'pass' },
    { label: 'Back-of-Envelope Calc', status: 'pass' },
    { label: 'API Design', status: 'pass' },
    { label: 'Database Schema', status: 'pass' },
    { label: 'Scalability Plan', status: 'partial' },
    { label: 'Reliability & Redundancy', status: 'pass' },
    { label: 'Monitoring & Alerts', status: 'fail' },
  ];

  function drawRadar() {
    if (!canvasEl) return;
    const ctx = canvasEl.getContext('2d');
    const w = canvasEl.width;
    const h = canvasEl.height;
    const cx = w / 2;
    const cy = h / 2;
    const maxR = Math.min(w, h) / 2 - 40;
    const n = radarLabels.length;

    ctx.clearRect(0, 0, w, h);

    // Draw grid rings
    for (let ring = 1; ring <= 5; ring++) {
      const r = (ring / 5) * maxR;
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = 'rgba(255,255,255,0.08)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Draw axes
    for (let i = 0; i < n; i++) {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + maxR * Math.cos(angle), cy + maxR * Math.sin(angle));
      ctx.strokeStyle = 'rgba(255,255,255,0.08)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Draw data polygon
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
      const idx = i % n;
      const angle = (Math.PI * 2 * idx) / n - Math.PI / 2;
      const r = (radarValues[idx] / 10) * maxR;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.fillStyle = 'rgba(168, 85, 247, 0.25)';
    ctx.fill();
    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw data points
    for (let i = 0; i < n; i++) {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const r = (radarValues[i] / 10) * maxR;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#fff';
      ctx.fill();
      ctx.strokeStyle = '#fbbf24';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Draw labels
    ctx.font = "11px 'Cinzel', serif";
    ctx.fillStyle = '#e0e7ff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for (let i = 0; i < n; i++) {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const r = maxR + 22;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      ctx.fillText(radarLabels[i].toUpperCase(), x, y);
    }
  }

  onMount(() => {
    drawRadar();
  });
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet" />
</svelte:head>

<div class="min-h-screen text-slate-200 relative overflow-x-hidden" style="font-family: 'Inter', sans-serif; background-color: #0f0c29;">
  <!-- Background effects -->
  <div class="fixed inset-0 pointer-events-none z-0">
    <div class="absolute inset-0" style="background: linear-gradient(to bottom right, #1e1b4b, #312e81, #0f0c29); opacity: 0.8;"></div>
    <div class="absolute -top-40 -right-40 w-96 h-96 bg-purple-900 rounded-full blur-3xl opacity-20"></div>
    <div class="absolute bottom-0 left-20 w-80 h-80 bg-blue-900 rounded-full blur-3xl opacity-20"></div>
    <div class="absolute top-1/4 left-1/4 w-2 h-2 bg-white rounded-full blur-sm opacity-60 animate-pulse"></div>
    <div class="absolute top-3/4 right-1/4 w-1 h-1 bg-amber-400 rounded-full blur-sm opacity-60 animate-pulse"></div>
  </div>

  <main class="relative z-10 container mx-auto px-6 py-10 max-w-7xl">
    <!-- Header -->
    <header class="text-center mb-12">
      <h1 class="text-4xl md:text-6xl font-bold mb-2" style="font-family: 'Cinzel', serif; background: linear-gradient(to right, #fde68a, #facc15, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        The Archmage Council Verdict
      </h1>
      <p class="text-indigo-200 text-lg tracking-wide uppercase opacity-80" style="font-family: 'Cinzel', serif;">
        System Design Evaluation • Candidate #8492
      </p>
    </header>

    <!-- Score + Radar section -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-12">
      <!-- Score orb -->
      <div class="lg:col-span-4 flex flex-col justify-center items-center">
        <div class="relative">
          <!-- Spinning dashed ring -->
          <div class="absolute inset-0 border-4 border-dashed border-purple-500/30 rounded-full spinning"></div>
          <div class="absolute -inset-4 border border-indigo-500/30 rounded-full spinning-reverse"></div>
          <!-- Score circle -->
          <div class="w-48 h-48 md:w-64 md:h-64 rounded-full flex flex-col items-center justify-center z-10 relative border-2 border-purple-500 score-orb">
            <span class="text-7xl md:text-8xl font-bold text-white cinzel-font score-glow">
              8<span class="text-4xl text-gray-400">/10</span>
            </span>
            <span class="text-purple-400 text-lg mt-2 tracking-widest uppercase cinzel-font">Mastery</span>
          </div>
        </div>
        <div class="mt-8 text-center space-y-2">
          <div class="inline-flex items-center px-4 py-1 rounded-full text-green-300 text-sm font-medium passed-badge">
            ✅ Passed Assessment
          </div>
          <p class="text-indigo-300 text-sm max-w-xs mx-auto italic">
            "The candidate weaves logic with exceptional clarity, though their scaling incantations require more potency."
          </p>
        </div>
      </div>

      <!-- Radar chart + attribute stats -->
      <div class="lg:col-span-8 rounded-2xl p-6 shadow-xl relative overflow-hidden arcane-card">
        <div class="absolute top-0 left-0 w-16 h-16 border-t-2 border-l-2 border-amber-500/50 rounded-tl-lg"></div>
        <div class="absolute bottom-0 right-0 w-16 h-16 border-b-2 border-r-2 border-amber-500/50 rounded-br-lg"></div>
        <h3 class="text-xl mb-6 flex items-center gap-2 text-amber-100 cinzel-font">
          ⬠ Arcane Attributes
        </h3>
        <div class="flex flex-col md:flex-row items-center gap-8">
          <div class="w-full md:w-2/3 flex justify-center">
            <canvas bind:this={canvasEl} width="350" height="300"></canvas>
          </div>
          <div class="w-full md:w-1/3 space-y-4">
            {#each attributes as attr (attr.label)}
              <div class="flex justify-between items-center border-b border-indigo-800 pb-2">
                <span class="text-indigo-200">{attr.label}</span>
                <span class="text-white font-bold">{attr.value}</span>
              </div>
            {/each}
          </div>
        </div>
      </div>
    </div>

    <!-- Council Feedback + Evaluation Rubric -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left: Feedback -->
      <div class="lg:col-span-2 space-y-6">
        <h2 class="text-2xl text-white mb-4 flex items-center cinzel-font">
          ✨ Council's Feedback
        </h2>

        <div class="grid md:grid-cols-2 gap-6">
          <!-- Strengths (parchment card) -->
          <div class="rounded-lg p-1 shadow-lg parchment-card" style="transform: rotate(-1deg);">
            <div class="border-2 border-dashed rounded h-full p-5" style="border-color: rgba(120, 53, 15, 0.2);">
              <h3 class="font-bold text-lg mb-3 flex items-center text-amber-900 cinzel-font">
                👍 Strengths
              </h3>
              <ul class="space-y-2 text-sm leading-relaxed text-slate-800">
                {#each strengths as s (s)}
                  <li class="flex items-start">
                    <span class="text-amber-700 mr-2 flex-shrink-0">•</span>
                    <span>{s}</span>
                  </li>
                {/each}
              </ul>
            </div>
          </div>

          <!-- Weaknesses (parchment card) -->
          <div class="rounded-lg p-1 shadow-lg parchment-card" style="transform: rotate(1deg);">
            <div class="border-2 border-dashed rounded h-full p-5" style="border-color: rgba(120, 53, 15, 0.2);">
              <h3 class="font-bold text-lg mb-3 flex items-center text-amber-900 cinzel-font">
                👎 Weaknesses
              </h3>
              <ul class="space-y-2 text-sm leading-relaxed text-slate-800">
                {#each weaknesses as w (w)}
                  <li class="flex items-start">
                    <span class="text-amber-700 mr-2 flex-shrink-0">•</span>
                    <span>{w}</span>
                  </li>
                {/each}
              </ul>
            </div>
          </div>
        </div>

        <!-- Grimoire of Improvement -->
        <div class="rounded-xl p-6 shadow-xl relative overflow-hidden grimoire-card">
          <div class="absolute top-0 right-0 p-4 opacity-10 text-8xl">⬆</div>
          <h3 class="text-amber-400 text-xl mb-4 cinzel-font">Grimoire of Improvement</h3>
          <div class="space-y-4 relative z-10">
            {#each improvements as item, i (item.title)}
              <div class="flex items-start gap-4">
                <div class="bg-indigo-600 rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 text-white font-bold">{i + 1}</div>
                <div>
                  <h4 class="text-white font-semibold">{item.title}</h4>
                  <p class="text-indigo-300 text-sm">{item.desc}</p>
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>

      <!-- Right: Evaluation Rubric -->
      <div class="lg:col-span-1">
        <div class="rounded-xl p-6 h-full rubric-card">
          <h2 class="text-xl text-white mb-6 border-b pb-4 cinzel-font" style="border-color: rgba(255,255,255,0.1);">
            Evaluation Rubric
          </h2>
          <div class="space-y-4">
            {#each rubric as item (item.label)}
              <div class="flex items-center justify-between group">
                <span class="text-gray-300 group-hover:text-white transition-colors">{item.label}</span>
                {#if item.status === 'pass'}
                  <span class="text-green-400 text-xl">✅</span>
                {:else if item.status === 'partial'}
                  <span class="text-amber-500 text-xl">⊖</span>
                {:else}
                  <span class="text-red-500 text-xl">❌</span>
                {/if}
              </div>
            {/each}
          </div>
          <div class="mt-8 pt-6 space-y-3" style="border-top: 1px solid rgba(255,255,255,0.1);">
            <button class="w-full py-3 px-4 rounded font-bold uppercase tracking-wider flex justify-center items-center gap-2 text-black shadow-lg transition-all active:scale-95 cinzel-font transcript-btn">
              📜 View Detailed Transcript
            </button>
            <button class="w-full py-3 px-4 rounded font-bold uppercase tracking-wider text-sm text-indigo-200 transition-all cinzel-font retake-btn">
              Retake Challenge
            </button>
          </div>
        </div>
      </div>
    </div>
  </main>
</div>

<style>
  .cinzel-font {
    font-family: 'Cinzel', serif;
  }

  .score-orb {
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(12px);
    box-shadow: 0 0 20px rgba(168, 85, 247, 0.4);
  }

  .score-glow {
    text-shadow: 0 0 10px rgba(168, 85, 247, 0.8);
  }

  .passed-badge {
    background: rgba(20, 83, 45, 0.4);
    border: 1px solid rgba(34, 197, 94, 0.5);
  }

  .arcane-card {
    background: rgba(15, 23, 42, 0.4);
    backdrop-filter: blur(4px);
    border: 1px solid rgba(99, 102, 241, 0.3);
  }

  .parchment-card {
    background: #eaddcf;
  }

  .parchment-card:hover {
    transform: rotate(0deg) !important;
    transition: transform 0.3s ease;
  }

  .grimoire-card {
    background: linear-gradient(to right, #1e293b, #0f172a);
    border: 1px solid rgba(99, 102, 241, 0.4);
    box-shadow: 0 0 15px rgba(245, 158, 11, 0.3);
  }

  .rubric-card {
    background: rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .transcript-btn {
    background: linear-gradient(135deg, #fbbf24, #d97706);
    box-shadow: 0 0 15px rgba(245, 158, 11, 0.3);
  }

  .retake-btn {
    background: transparent;
    border: 1px solid rgba(129, 140, 248, 0.5);
  }

  .spinning {
    animation: spin 10s linear infinite;
  }

  .spinning-reverse {
    animation: spin 15s linear infinite reverse;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>
