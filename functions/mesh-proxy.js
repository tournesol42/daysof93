export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const filename = url.searchParams.get('file');

  if (!filename || !filename.endsWith('.glb')) {
    return new Response('Invalid file', { status: 400 });
  }

  // Fetch from Storage API (no hotlink protection) using API key
  const storageUrl = 'https://storage.bunnycdn.com/daysof93-videos/meshes/' + filename;
  const res = await fetch(storageUrl, {
    headers: {
      'AccessKey': env.BUNNY_STORAGE_KEY,
    },
  });

  if (!res.ok) {
    return new Response('Storage error: ' + res.status, { status: 404 });
  }

  return new Response(res.body, {
    status: 200,
    headers: {
      'Content-Type': 'model/gltf-binary',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'public, max-age=86400',
    },
  });
}
