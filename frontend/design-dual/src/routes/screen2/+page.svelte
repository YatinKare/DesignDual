<script lang="ts">
  import { onMount, tick } from 'svelte';

  const phaseOrder: string[] = ['clarify', 'estimate', 'design', 'explain'];
  const phaseLabel: Record<string, string> = {
    clarify: 'Clarify',
    estimate: 'Estimate',
    design: 'Design',
    explain: 'Tradeoffs',
  };

  const demoReport = {
    submission_id: 'sub_demo_8492',
    verdict: 'Lean Hire',
    overall_score: 8,
    summary: 'Strong communication and structure; scale and failure-mode depth need tightening.',
    problem: {
      id: 'url-shortener',
      name: 'Design a URL Shortener',
      difficulty: 'Easy',
    },
    phase_times: {
      clarify: 458,
      estimate: 524,
      design: 910,
      explain: 438,
    },
    radar: {
      clarity: 9.2,
      structure: 8.5,
      power: 6.8,
      wisdom: 7.5,
      speed: 7.9,
      security: 7.1,
    },
    phase_scores: [
      {
        phase: 'clarify',
        score: 9,
        bullets: ['Captured core requirements', 'Clarified expiration and alias constraints'],
      },
      {
        phase: 'estimate',
        score: 7,
        bullets: ['Reasonable traffic assumptions', 'Replication factor was not called out'],
      },
      {
        phase: 'design',
        score: 8,
        bullets: ['Clean service split and schema', 'Cache invalidation strategy stayed vague'],
      },
      {
        phase: 'explain',
        score: 6,
        bullets: ['Explained happy path clearly', 'Did not cover region outage recovery'],
      },
    ],
    evidence: [
      {
        phase: 'clarify',
        snapshot_url: '/assets/thumbnail.jpg',
        transcripts: [
          { timestamp_sec: 48, text: 'I will support custom aliases and default expiry of 30 days.' },
          { timestamp_sec: 126, text: 'Read latency should stay under 50ms at p95.' },
        ],
        noticed: {
          strength: 'Clearly framed functional and non-functional scope before drawing.',
          issue: 'Did not ask about expected write amplification from analytics events.',
        },
      },
      {
        phase: 'estimate',
        snapshot_url: '/assets/thumbnail.png',
        transcripts: [
          { timestamp_sec: 72, text: 'Assume 100M new links per day and 20:1 read/write ratio.' },
          { timestamp_sec: 190, text: 'Storage estimate includes URL and metadata but not replicas.' },
        ],
        noticed: {
          strength: 'Good back-of-envelope throughput and storage calculation flow.',
          issue: 'Replication and index overhead missing from total capacity number.',
        },
      },
      {
        phase: 'design',
        snapshot_url: '/assets/thumbnail.jpg',
        transcripts: [
          { timestamp_sec: 96, text: 'Routing through API gateway, write service, and metadata store.' },
          { timestamp_sec: 281, text: 'I would add a Redis layer for hot links.' },
        ],
        noticed: {
          strength: 'Service boundaries and DB schema were easy to follow from the diagram.',
          issue: 'Cache key strategy and invalidation path were not specified.',
        },
      },
      {
        phase: 'explain',
        snapshot_url: '/assets/thumbnail.png',
        transcripts: [],
        noticed: {
          strength: 'Tradeoff framing was concise and prioritized user latency.',
          issue: 'No explicit failure-mode response during regional outage.',
        },
      },
    ],
    strengths: [
      { phase: 'clarify', text: 'Requirements were organized before assumptions were locked in.', timestamp_sec: 42 },
      { phase: 'design', text: 'Diagram showed clear read/write path separation.', timestamp_sec: 258 },
      { phase: 'explain', text: 'Tradeoffs were explained in order of user impact.', timestamp_sec: 360 },
    ],
    weaknesses: [
      { phase: 'estimate', text: 'Storage estimate missed replication and index overhead.', timestamp_sec: 182 },
      { phase: 'design', text: 'No cache invalidation strategy shown between API and DB.', timestamp_sec: 284 },
      { phase: 'explain', text: 'Consistency model for alias updates was not defined.', timestamp_sec: 391 },
    ],
    rubric: [
      { label: 'Requirements Gathering', score: 9, status: 'pass', computed_from: ['clarify'] },
      { label: 'Back-of-Envelope Calc', score: 7, status: 'partial', computed_from: ['estimate'] },
      { label: 'API Design', score: 8, status: 'pass', computed_from: ['design'] },
      { label: 'Database Schema', score: 8, status: 'pass', computed_from: ['design'] },
      { label: 'Scalability Plan', score: 6, status: 'partial', computed_from: ['design', 'explain'] },
      { label: 'Reliability & Redundancy', score: 6, status: 'partial', computed_from: ['explain'] },
      { label: 'Monitoring & Alerts', score: 5, status: 'fail', computed_from: ['explain'] },
    ],
    next_attempt_plan: [
      {
        fix: 'Add a concrete caching strategy for read-heavy endpoints.',
        why: 'Latency and DB load both hinge on cache hit-rate and invalidation rules.',
        do_next_time: ['Name cache keys by alias hash + version', 'Define cache-aside write path', 'Call out invalidation trigger events'],
      },
      {
        fix: 'Include replica and index overhead in capacity estimates.',
        why: 'Ignoring overhead underestimates storage and cluster footprint.',
        do_next_time: ['Calculate base record size', 'Apply replication factor', 'Add 20-30% index and metadata buffer'],
      },
      {
        fix: 'State outage and consistency behavior explicitly.',
        why: 'Interviewers look for failure-mode handling, not only happy-path design.',
        do_next_time: ['Define write quorum model', 'Describe regional failover policy', 'Specify recovery RPO/RTO target'],
      },
    ],
    follow_up_questions: [
      'How would you handle cache invalidation across regions?',
      'Which consistency model would you use for custom alias updates?',
      'What should happen to writes during a single-region outage?',
    ],
    transcript_highlights: [
      { phase: 'clarify', timestamp_sec: 48, text: 'Support custom aliases and default expiry of 30 days.' },
      { phase: 'estimate', timestamp_sec: 72, text: 'Assume 100M new links/day and 20:1 read/write ratio.' },
      { phase: 'design', timestamp_sec: 281, text: 'I would add a Redis layer for hot links.' },
      { phase: 'explain', timestamp_sec: 391, text: 'Consistency for alias updates needs stricter guarantees.' },
    ],
    full_transcript: [
      { phase: 'clarify', timestamp_sec: 48, text: 'I will support custom aliases and default expiry of 30 days.' },
      { phase: 'clarify', timestamp_sec: 126, text: 'Read latency should stay under 50ms at p95.' },
      { phase: 'estimate', timestamp_sec: 72, text: 'Assume 100M new links per day and 20:1 read/write ratio.' },
      { phase: 'estimate', timestamp_sec: 190, text: 'Storage estimate includes URL and metadata but not replicas.' },
      { phase: 'design', timestamp_sec: 96, text: 'Routing through API gateway, write service, and metadata store.' },
      { phase: 'design', timestamp_sec: 281, text: 'I would add a Redis layer for hot links.' },
      { phase: 'explain', timestamp_sec: 360, text: 'Tradeoff priority is latency first, then consistency guarantees.' },
      { phase: 'explain', timestamp_sec: 391, text: 'Consistency model for alias updates was not fully specified.' },
    ],
    reference_outline: {
      sections: [
        {
          title: 'Core Components',
          bullets: ['API gateway + auth/rate limits', 'URL write/read services', 'Metadata store + cache tier', 'Background analytics pipeline'],
        },
        {
          title: 'Data Model Focus',
          bullets: ['Alias -> destination mapping', 'TTL and soft-delete policy', 'Versioned records for update safety'],
        },
        {
          title: 'Scale & Reliability Checks',
          bullets: ['Partitioning strategy at 100M/day', 'Cross-region replication and failover', 'Monitoring: p95 latency, hit rate, error budget'],
        },
      ],
    },
  };

  const radarAxes = ['Clarity', 'Structure', 'Power', 'Wisdom'];

  let canvasEl: HTMLCanvasElement | null = null;
  let isLoading = $state(false);
  let loadError = $state('');
  let report = $state<any>(demoReport);
  let selectedPhase = $state('clarify');
  let showDetailedTranscript = $state(false);
  let showReferenceOutline = $state(false);
  let jumpMessage = $state('');

  let activePhase = $derived(
    report.evidence.some((item: any) => item.phase === selectedPhase)
      ? selectedPhase
      : (report.evidence[0]?.phase ?? 'clarify')
  );

  let selectedEvidence = $derived<any>(
    report.evidence.find((item: any) => item.phase === activePhase) ?? report.evidence[0] ?? null
  );

  function scoreStatusIcon(status: string) {
    if (status === 'pass') return '✅';
    if (status === 'partial') return '⊖';
    return '❌';
  }

  function formatTimestamp(seconds: number) {
    const total = Number.isFinite(seconds) ? Math.max(0, Math.floor(seconds)) : 0;
    const mins = Math.floor(total / 60).toString().padStart(2, '0');
    const secs = (total % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  }

  function formatDuration(seconds: number) {
    const total = Number.isFinite(seconds) ? Math.max(0, Math.floor(seconds)) : 0;
    const mins = Math.floor(total / 60);
    const secs = total % 60;
    return `${mins}m ${secs}s`;
  }

  function totalTimeSeconds() {
    return phaseOrder.reduce((sum, phase) => sum + (report.phase_times?.[phase] ?? 0), 0);
  }

  function jumpToTranscript(phase: string, timestampSec: number) {
    selectedPhase = phase;
    jumpMessage = `Jumped to ${phaseLabel[phase]} @ ${formatTimestamp(timestampSec)}`;
  }

  function formatComputedFrom(phases: string[]) {
    return phases.map((phase) => phaseLabel[phase] ?? phase).join(' + ');
  }

  function normalizeSubmissionPayload(payload: unknown) {
    if (!payload || typeof payload !== 'object') return demoReport;

    const payloadObj = payload as Record<string, any>;
    const source = payloadObj.result && typeof payloadObj.result === 'object' ? payloadObj.result : payloadObj;
    const merged: any = structuredClone(demoReport);

    merged.submission_id = source.submission_id ?? payloadObj.submission_id ?? merged.submission_id;
    merged.verdict = source.verdict ?? merged.verdict;
    merged.summary = source.summary ?? merged.summary;
    merged.overall_score = Number.isFinite(source.overall_score) ? source.overall_score : merged.overall_score;

    if (source.problem && typeof source.problem === 'object') {
      merged.problem = {
        id: source.problem.id ?? merged.problem.id,
        name: source.problem.name ?? merged.problem.name,
        difficulty: source.problem.difficulty ?? merged.problem.difficulty,
      };
    }

    if (source.phase_times) {
      let phaseTimes: Record<string, any> | string = source.phase_times;
      if (typeof phaseTimes === 'string') {
        try {
          phaseTimes = JSON.parse(phaseTimes) as Record<string, any>;
        } catch {
          phaseTimes = {};
        }
      }

      if (phaseTimes && typeof phaseTimes === 'object') {
        for (const phase of phaseOrder) {
          if (Number.isFinite((phaseTimes as Record<string, any>)[phase])) {
            merged.phase_times[phase] = phaseTimes[phase];
          }
        }
      }
    }

    if (source.radar && typeof source.radar === 'object') {
      merged.radar = {
        ...merged.radar,
        clarity: Number.isFinite(source.radar.clarity) ? source.radar.clarity : merged.radar.clarity,
        structure: Number.isFinite(source.radar.structure) ? source.radar.structure : merged.radar.structure,
        power: Number.isFinite(source.radar.power) ? source.radar.power : merged.radar.power,
        wisdom: Number.isFinite(source.radar.wisdom) ? source.radar.wisdom : merged.radar.wisdom,
        speed: Number.isFinite(source.radar.speed) ? source.radar.speed : merged.radar.speed,
        security: Number.isFinite(source.radar.security) ? source.radar.security : merged.radar.security,
      };
    }

    if (Array.isArray(source.phase_scores) && source.phase_scores.length > 0) {
      merged.phase_scores = source.phase_scores;
    }

    if (Array.isArray(source.evidence) && source.evidence.length > 0) {
      merged.evidence = source.evidence;
    }

    if (Array.isArray(source.strengths) && source.strengths.length > 0) {
      merged.strengths = source.strengths;
    }

    if (Array.isArray(source.weaknesses) && source.weaknesses.length > 0) {
      merged.weaknesses = source.weaknesses;
    }

    if (Array.isArray(source.rubric) && source.rubric.length > 0) {
      merged.rubric = source.rubric;
    }

    if (Array.isArray(source.next_attempt_plan) && source.next_attempt_plan.length > 0) {
      merged.next_attempt_plan = source.next_attempt_plan;
    }

    if (Array.isArray(source.follow_up_questions) && source.follow_up_questions.length > 0) {
      merged.follow_up_questions = source.follow_up_questions;
    }

    if (Array.isArray(source.transcript_highlights) && source.transcript_highlights.length > 0) {
      merged.transcript_highlights = source.transcript_highlights;
    }

    if (Array.isArray(source.full_transcript) && source.full_transcript.length > 0) {
      merged.full_transcript = source.full_transcript;
    }

    if (source.reference_outline && typeof source.reference_outline === 'object') {
      merged.reference_outline = source.reference_outline;
    }

    return merged;
  }

  async function loadSubmission() {
    const params = new URLSearchParams(window.location.search);
    const submissionId = params.get('submission_id') || params.get('id');
    if (!submissionId) return;

    isLoading = true;
    loadError = '';

    try {
      const response = await fetch(`/api/submissions/${submissionId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch submission ${submissionId}`);
      }

      const payload: unknown = await response.json();
      report = normalizeSubmissionPayload(payload);
      await tick();
      drawRadar();
    } catch (error) {
      loadError = error instanceof Error ? error.message : 'Could not load submission. Showing demo data.';
    } finally {
      isLoading = false;
    }
  }

  function radarCanvas(node: HTMLCanvasElement) {
    canvasEl = node;
    drawRadar();

    return {
      destroy() {
        if (canvasEl === node) {
          canvasEl = null;
        }
      },
    };
  }

  function drawRadar() {
    if (!canvasEl) return;

    const ctx = canvasEl.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const displayWidth = 400;
    const displayHeight = 340;

    canvasEl.width = displayWidth * dpr;
    canvasEl.height = displayHeight * dpr;
    canvasEl.style.width = `${displayWidth}px`;
    canvasEl.style.height = `${displayHeight}px`;

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);

    const w = displayWidth;
    const h = displayHeight;
    const cx = w / 2;
    const cy = h / 2;
    const maxR = Math.min(w, h) / 2 - 56;
    const values = [report.radar.clarity, report.radar.structure, report.radar.power, report.radar.wisdom];
    const axisCount = radarAxes.length;

    ctx.clearRect(0, 0, w, h);

    for (let ring = 1; ring <= 5; ring++) {
      const r = (ring / 5) * maxR;
      ctx.beginPath();
      for (let i = 0; i <= axisCount; i++) {
        const idx = i % axisCount;
        const angle = (Math.PI * 2 * idx) / axisCount - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    for (let i = 0; i < axisCount; i++) {
      const angle = (Math.PI * 2 * i) / axisCount - Math.PI / 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + maxR * Math.cos(angle), cy + maxR * Math.sin(angle));
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    ctx.beginPath();
    for (let i = 0; i <= axisCount; i++) {
      const idx = i % axisCount;
      const angle = (Math.PI * 2 * idx) / axisCount - Math.PI / 2;
      const r = (values[idx] / 10) * maxR;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.fillStyle = 'rgba(245, 158, 11, 0.22)';
    ctx.fill();
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2;
    ctx.stroke();

    for (let i = 0; i < axisCount; i++) {
      const angle = (Math.PI * 2 * i) / axisCount - Math.PI / 2;
      const r = (values[i] / 10) * maxR;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#fef3c7';
      ctx.fill();
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    ctx.font = "11px 'Cinzel', serif";
    ctx.fillStyle = '#dbeafe';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for (let i = 0; i < axisCount; i++) {
      const angle = (Math.PI * 2 * i) / axisCount - Math.PI / 2;
      const r = maxR + 24;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      ctx.fillText(radarAxes[i].toUpperCase(), x, y);
    }
  }

  onMount(() => {
    loadSubmission();
    drawRadar();
    const onResize = () => drawRadar();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  });
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
</svelte:head>

<div class="min-h-screen text-slate-200 relative overflow-x-hidden" style="font-family: 'Inter', sans-serif; background-color: #0f0c29;">
  <div class="fixed inset-0 pointer-events-none z-0">
    <div class="absolute inset-0" style="background: radial-gradient(circle at 20% 20%, #1f2a44 0%, #171d33 40%, #0f0c29 100%); opacity: 0.9;"></div>
    <div class="absolute -top-48 right-0 w-[30rem] h-[30rem] bg-sky-800 rounded-full blur-3xl opacity-15"></div>
    <div class="absolute bottom-0 left-0 w-[24rem] h-[24rem] bg-amber-700 rounded-full blur-3xl opacity-10"></div>
  </div>

  <main class="relative z-10 container mx-auto px-4 md:px-6 py-8 md:py-10 max-w-7xl">
    <header class="mb-6">
      <h1 class="text-3xl md:text-5xl font-bold mb-2 cinzel-font title-gradient">Council Evaluation Report</h1>
      <p class="text-sm md:text-base text-slate-300">Submission: {report.submission_id}</p>
      {#if isLoading}
        <p class="text-sm text-amber-300 mt-2">Loading live result from backend...</p>
      {/if}
      {#if loadError}
        <p class="text-sm text-rose-300 mt-2">{loadError}</p>
      {/if}
    </header>

    <section class="grid grid-cols-1 xl:grid-cols-12 gap-4 mb-6">
      <div class="xl:col-span-4 rounded-2xl p-5 report-card">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Verdict</p>
            <p class="text-2xl font-bold text-white cinzel-font">{report.verdict}</p>
          </div>
          <div class="text-right">
            <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Score</p>
            <p class="text-4xl font-bold text-amber-300">{report.overall_score}<span class="text-lg text-slate-400">/10</span></p>
          </div>
        </div>
        <p class="text-sm text-slate-300 mt-3">{report.summary}</p>
        <div class="mt-4 pt-4 border-t border-slate-700/60 space-y-2 text-sm">
          <p><span class="text-slate-400">Problem:</span> {report.problem.name}</p>
          <p><span class="text-slate-400">Difficulty:</span> {report.problem.difficulty}</p>
          <p><span class="text-slate-400">Total time:</span> {formatDuration(totalTimeSeconds())}</p>
          <div class="flex flex-wrap gap-2 mt-2">
            {#each phaseOrder as phase (phase)}
              <span class="px-2 py-1 rounded-md text-xs phase-badge">{phaseLabel[phase]}: {formatDuration(report.phase_times?.[phase] ?? 0)}</span>
            {/each}
          </div>
        </div>
      </div>

      <div class="xl:col-span-8 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {#each report.phase_scores as card (card.phase)}
          <article class="rounded-2xl p-4 phase-card">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-semibold text-white">{phaseLabel[card.phase]}</h3>
              <span class="text-lg font-bold text-amber-300">{card.score}/10</span>
            </div>
            <ul class="space-y-1 text-xs text-slate-300">
              {#each card.bullets as bullet (bullet)}
                <li>- {bullet}</li>
              {/each}
            </ul>
          </article>
        {/each}
      </div>
    </section>

    <section class="grid grid-cols-1 xl:grid-cols-12 gap-6 mb-6">
      <article class="xl:col-span-5 rounded-2xl p-5 report-card">
        <h2 class="text-lg md:text-xl mb-4 text-amber-200 cinzel-font">Radar (4 Dimensions)</h2>
        <div class="flex flex-col items-center">
          <canvas use:radarCanvas></canvas>
          <div class="grid grid-cols-2 gap-3 w-full max-w-md text-sm mt-3">
            <div class="metric-chip">Clarity: <span>{report.radar.clarity}/10</span></div>
            <div class="metric-chip">Structure: <span>{report.radar.structure}/10</span></div>
            <div class="metric-chip">Power: <span>{report.radar.power}/10</span></div>
            <div class="metric-chip">Wisdom: <span>{report.radar.wisdom}/10</span></div>
          </div>
          <div class="flex flex-wrap gap-2 mt-4 text-xs">
            <span class="px-2 py-1 rounded-md secondary-chip">Speed: {report.radar.speed}/10</span>
            <span class="px-2 py-1 rounded-md secondary-chip">Security: {report.radar.security}/10</span>
          </div>
        </div>
      </article>

      <article class="xl:col-span-7 rounded-2xl p-5 report-card">
        <h2 class="text-lg md:text-xl mb-4 text-amber-200 cinzel-font">Evidence Rail</h2>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          {#each report.evidence as item (item.phase)}
            <button
              class="text-left rounded-xl overflow-hidden evidence-tile"
              class:evidence-selected={activePhase === item.phase}
              onclick={() => selectedPhase = item.phase}
              type="button"
            >
              <img src={item.snapshot_url} alt={`${phaseLabel[item.phase]} snapshot`} class="w-full h-20 object-cover" />
              <div class="px-2 py-2 bg-slate-900/80">
                <p class="text-xs uppercase tracking-wide text-slate-300">{phaseLabel[item.phase]}</p>
              </div>
            </button>
          {/each}
        </div>

        {#if selectedEvidence}
          <div class="rounded-xl p-4 bg-slate-950/55 border border-slate-700/60 space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="font-semibold text-white">Selected: {phaseLabel[selectedEvidence.phase]}</h3>
              <span class="text-xs text-slate-400">Snapshot + transcript-backed observations</span>
            </div>

            {#if selectedEvidence.transcripts.length > 0}
              <div class="space-y-2">
                {#each selectedEvidence.transcripts.slice(0, 2) as snippet (`${selectedEvidence.phase}-${snippet.timestamp_sec}`)}
                  <div class="rounded-lg bg-slate-900/80 border border-slate-700/60 p-3">
                    <p class="text-sm text-slate-200">"{snippet.text}"</p>
                    <button
                      type="button"
                      class="text-xs text-amber-300 mt-2 hover:text-amber-200 underline"
                      onclick={() => jumpToTranscript(selectedEvidence.phase, snippet.timestamp_sec)}
                    >
                      Jump to {formatTimestamp(snippet.timestamp_sec)}
                    </button>
                  </div>
                {/each}
              </div>
            {:else}
              <p class="text-sm text-slate-300">No audio recorded.</p>
            {/if}

            <div class="grid sm:grid-cols-2 gap-3 text-sm">
              <div class="rounded-lg border border-emerald-700/30 bg-emerald-950/25 p-3">
                <p class="text-xs uppercase tracking-wide text-emerald-300 mb-1">What the agent noticed: strength</p>
                <p class="text-emerald-100">{selectedEvidence.noticed.strength}</p>
              </div>
              <div class="rounded-lg border border-rose-700/30 bg-rose-950/20 p-3">
                <p class="text-xs uppercase tracking-wide text-rose-300 mb-1">What the agent noticed: issue</p>
                <p class="text-rose-100">{selectedEvidence.noticed.issue}</p>
              </div>
            </div>
          </div>
        {/if}

        <div id="transcript-highlights" class="mt-4">
          <h3 class="text-sm font-semibold text-slate-200 mb-2">Transcript highlights</h3>
          <ul class="space-y-2">
            {#each report.transcript_highlights.slice(0, 6) as item (`hl-${item.phase}-${item.timestamp_sec}`)}
              <li class="text-sm text-slate-300 bg-slate-950/35 border border-slate-700/40 rounded-md p-2">
                <span class="text-amber-300">[{phaseLabel[item.phase]} {formatTimestamp(item.timestamp_sec)}]</span>
                <span class="ml-2">{item.text}</span>
              </li>
            {/each}
          </ul>
          <button
            class="mt-3 px-3 py-2 rounded-md text-sm text-slate-100 border border-slate-500/60 hover:border-slate-300"
            type="button"
            onclick={() => showDetailedTranscript = !showDetailedTranscript}
          >
            {showDetailedTranscript ? 'Hide detailed transcript' : 'View detailed transcript'}
          </button>

          {#if showDetailedTranscript}
            <ul class="space-y-2 mt-3 max-h-56 overflow-y-auto pr-2">
              {#each report.full_transcript as item (`full-${item.phase}-${item.timestamp_sec}`)}
                <li class="text-xs text-slate-300 border-l-2 border-slate-600 pl-3 py-1">
                  <span class="text-slate-400">[{phaseLabel[item.phase]} {formatTimestamp(item.timestamp_sec)}]</span> {item.text}
                </li>
              {/each}
            </ul>
          {/if}
        </div>
      </article>
    </section>

    <section class="grid grid-cols-1 xl:grid-cols-12 gap-6 mb-6">
      <article class="xl:col-span-7 rounded-2xl p-5 report-card">
        <div class="grid md:grid-cols-2 gap-4">
          <div class="feedback-card">
            <h3 class="text-lg font-semibold text-emerald-200 mb-3">Strengths</h3>
            <ul class="space-y-2">
              {#each report.strengths as item (`strength-${item.phase}-${item.text}`)}
                <li class="text-sm text-slate-200">
                  <button type="button" class="phase-tag" onclick={() => selectedPhase = item.phase}>
                    [{phaseLabel[item.phase]}]
                  </button>
                  <span class="ml-1">{item.text}</span>
                  {#if Number.isFinite(item.timestamp_sec)}
                    <button
                      type="button"
                      class="ml-2 text-xs text-amber-300 underline"
                      onclick={() => jumpToTranscript(item.phase, item.timestamp_sec)}
                    >
                      {formatTimestamp(item.timestamp_sec)}
                    </button>
                  {/if}
                </li>
              {/each}
            </ul>
          </div>
          <div class="feedback-card">
            <h3 class="text-lg font-semibold text-rose-200 mb-3">Weaknesses</h3>
            <ul class="space-y-2">
              {#each report.weaknesses as item (`weak-${item.phase}-${item.text}`)}
                <li class="text-sm text-slate-200">
                  <button type="button" class="phase-tag" onclick={() => selectedPhase = item.phase}>
                    [{phaseLabel[item.phase]}]
                  </button>
                  <span class="ml-1">{item.text}</span>
                  {#if Number.isFinite(item.timestamp_sec)}
                    <button
                      type="button"
                      class="ml-2 text-xs text-amber-300 underline"
                      onclick={() => jumpToTranscript(item.phase, item.timestamp_sec)}
                    >
                      {formatTimestamp(item.timestamp_sec)}
                    </button>
                  {/if}
                </li>
              {/each}
            </ul>
          </div>
        </div>
        {#if jumpMessage}
          <p class="mt-4 text-xs text-amber-200">{jumpMessage}</p>
        {/if}
      </article>

      <article class="xl:col-span-5 rounded-2xl p-5 report-card">
        <h2 class="text-lg md:text-xl mb-4 text-amber-200 cinzel-font">Rubric (Score + Computation)</h2>
        <div class="space-y-3">
          {#each report.rubric as item (item.label)}
            <div class="rubric-row">
              <div>
                <p class="text-sm text-slate-100">{item.label}</p>
                <p class="text-xs text-slate-400" title={`Derived mostly from ${formatComputedFrom(item.computed_from)}`}>
                  Derived from {formatComputedFrom(item.computed_from)}
                </p>
              </div>
              <div class="text-right">
                <p class="text-sm font-semibold text-amber-300">{item.score}/10 {scoreStatusIcon(item.status)}</p>
              </div>
            </div>
          {/each}
        </div>
      </article>
    </section>

    <section class="grid grid-cols-1 xl:grid-cols-12 gap-6">
      <article class="xl:col-span-7 rounded-2xl p-5 report-card">
        <h2 class="text-lg md:text-xl mb-4 text-amber-200 cinzel-font">Next Attempt Plan (Top 3 Fixes)</h2>
        <div class="space-y-4">
          {#each report.next_attempt_plan as item, index (`plan-${item.fix}`)}
            <div class="rounded-xl border border-slate-700/60 bg-slate-950/45 p-4">
              <p class="text-sm uppercase tracking-wide text-slate-400">Fix #{index + 1}</p>
              <h3 class="text-base font-semibold text-white mt-1">{item.fix}</h3>
              <p class="text-sm text-slate-300 mt-1"><span class="text-slate-400">Why it matters:</span> {item.why}</p>
              <div class="mt-2">
                <p class="text-xs uppercase tracking-wide text-slate-400 mb-1">Do this next time</p>
                <ul class="space-y-1 text-sm text-slate-200">
                  {#each item.do_next_time as step (`step-${step}`)}
                    <li>- {step}</li>
                  {/each}
                </ul>
              </div>
            </div>
          {/each}
        </div>
      </article>

      <article class="xl:col-span-5 rounded-2xl p-5 report-card">
        <h2 class="text-lg md:text-xl mb-4 text-amber-200 cinzel-font">Follow-up Questions You Would Be Asked</h2>
        <ul class="space-y-2 text-sm text-slate-200 mb-5">
          {#each report.follow_up_questions as q (q)}
            <li class="rounded-md border border-slate-700/50 bg-slate-950/45 p-3">- {q}</li>
          {/each}
        </ul>

        <button
          class="w-full mb-3 py-2 px-3 rounded-md text-sm border border-amber-500/60 text-amber-100 hover:bg-amber-600/15"
          type="button"
          onclick={() => showReferenceOutline = !showReferenceOutline}
        >
          {showReferenceOutline ? 'Hide Council Reference Outline' : 'Reveal Council Reference Spell'}
        </button>

        {#if showReferenceOutline}
          <div class="space-y-3 rounded-xl border border-amber-500/30 bg-amber-950/10 p-4">
            <p class="text-xs text-amber-200">Outline only. Components and structure, not a full copyable answer.</p>
            {#each report.reference_outline.sections as section (section.title)}
              <div>
                <h3 class="text-sm font-semibold text-amber-100">{section.title}</h3>
                <ul class="text-sm text-slate-200 mt-1 space-y-1">
                  {#each section.bullets as bullet (bullet)}
                    <li>- {bullet}</li>
                  {/each}
                </ul>
              </div>
            {/each}
          </div>
        {/if}
      </article>
    </section>
  </main>
</div>

<style>
  .cinzel-font {
    font-family: 'Cinzel', serif;
  }

  .title-gradient {
    background: linear-gradient(90deg, #fef3c7 0%, #f59e0b 45%, #fcd34d 100%);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .report-card {
    background: rgba(15, 23, 42, 0.55);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(148, 163, 184, 0.25);
    box-shadow: 0 12px 32px rgba(2, 6, 23, 0.35);
  }

  .phase-card {
    background: linear-gradient(165deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9));
    border: 1px solid rgba(51, 65, 85, 0.9);
  }

  .phase-badge {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(100, 116, 139, 0.5);
  }

  .metric-chip {
    border: 1px solid rgba(71, 85, 105, 0.8);
    border-radius: 0.5rem;
    padding: 0.45rem 0.6rem;
    color: #e2e8f0;
    background: rgba(15, 23, 42, 0.5);
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
  }

  .metric-chip span {
    color: #fcd34d;
    font-weight: 700;
  }

  .secondary-chip {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(71, 85, 105, 0.8);
    color: #cbd5e1;
  }

  .evidence-tile {
    border: 1px solid rgba(71, 85, 105, 0.7);
    transition: all 0.15s ease-in-out;
  }

  .evidence-tile:hover {
    transform: translateY(-1px);
    border-color: rgba(245, 158, 11, 0.6);
  }

  .evidence-selected {
    border-color: rgba(245, 158, 11, 0.85);
    box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.4);
  }

  .feedback-card {
    border: 1px solid rgba(71, 85, 105, 0.7);
    border-radius: 0.75rem;
    background: rgba(2, 6, 23, 0.35);
    padding: 1rem;
  }

  .phase-tag {
    color: #fcd34d;
    border: 1px solid rgba(245, 158, 11, 0.55);
    border-radius: 0.3rem;
    font-size: 0.72rem;
    padding: 0.05rem 0.35rem;
    background: rgba(120, 53, 15, 0.18);
  }

  .rubric-row {
    border: 1px solid rgba(71, 85, 105, 0.7);
    border-radius: 0.7rem;
    padding: 0.7rem 0.8rem;
    background: rgba(2, 6, 23, 0.3);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
  }
</style>
