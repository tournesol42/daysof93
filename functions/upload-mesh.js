export async function onRequestPost(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const filename = url.searchParams.get('filename');

  if (!filename || !filename.endsWith('.glb')) {
    return new Response('Missing or invalid filename', { status: 400 });
  }

  const body = await request.arrayBuffer();

  const bunnyRes = await fetch(
    'https://storage.de.bunnycdn.com/daysof93-videos/meshes/' + filename,
    {
      method: 'PUT',
      headers: {
        'AccessKey': env.BUNNY_STORAGE_KEY,
        'Content-Type': 'application/octet-stream',
      },
      body: body,
    }
  );

  if (!bunnyRes.ok) {
    return new Response('Bunny error: ' + bunnyRes.status, { status: 502 });
  }

  const cdnUrl = 'https://daysof93-cdn.b-cdn.net/meshes/' + filename;
  return new Response(JSON.stringify({ url: cdnUrl }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}
