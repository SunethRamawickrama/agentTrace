<script lang="ts">
	import '../app.css';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<div class="min-h-screen bg-slate-950">
	<nav class="border-b border-slate-800 bg-slate-900 px-6 py-3">
		<div class="flex items-center gap-6">
			<a href="/traces" class="text-lg font-bold text-slate-100">agentTrace</a>
			<a href="/traces" class="text-sm text-slate-400 hover:text-slate-200">Traces</a>
		</div>
	</nav>
	<main>
		{@render children()}
	</main>
</div>
