export const ssr = false;

export async function load({ fetch }) {
	const res = await fetch('/api/traces');
	const data = await res.json();
	return { traces: data.traces };
}
