import { listIncidents } from '@/lib/api'

export default async function Home() {
	const incidents = await listIncidents()

	return (
		<main className='mx-auto max-w-6xl p-8'>
			<p className='text-sm font-semibold text-blue-600'>RELAYOPS</p>
			<h1 className='mt-2 text-3xl font-semibold'>Incident queue</h1>
			<div className='mt-8 grid gap-4'>
				{incidents.map((incident) => (
					<article key={incident.id} className='rounded-xl border p-5'>
						<div className='flex justify-between gap-4'>
							<h2 className='font-semibold'>{incident.title}</h2>
							<span>{incident.status}</span>
						</div>
						<p className='mt-2 text-sm text-slate-600'>{incident.summary}</p>
					</article>
				))}
			</div>
		</main>
	)
}
