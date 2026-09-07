import { z } from 'zod'

const Incident = z.object({
	id: z.uuid(),
	tenant_id: z.uuid(),
	scenario_key: z.string().nullable(),
	title: z.string(),
	summary: z.string(),
	severity: z.string(),
	status: z.string(),
	created_at: z.string(),
	updated_at: z.string(),
})

export type Incident = z.infer<typeof Incident>

const base = process.env.NEXT_PUBLIC_API_BASE_URL!

export async function listIncidents(): Promise<Incident[]> {
	const response = await fetch(`${base}/incidents`, { cache: 'no-store' })
	if (!response.ok) throw new Error('Could not load incidents')
	return z.array(Incident).parse(await response.json())
}
