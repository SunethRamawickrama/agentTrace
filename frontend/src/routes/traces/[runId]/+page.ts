import { error } from '@sveltejs/kit';

export const ssr = false;

export async function load({ params, fetch }) {
	const res = await fetch(`/api/traces/${params.runId}`);
	if (!res.ok) throw error(404, 'Trace not found');
	const trace = await res.json();
	return { trace };
}
