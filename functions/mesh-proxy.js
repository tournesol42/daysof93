export async function onRequestGet(context) {
  const { request } = context;
  const url = new URL(request.url);
  const filename = url.searchParams.get('file');

  if (!filename || !filename.endsWith('.glb')) {
    return new Response('Invalid file', { status: 400 });
  }

  const bunnyUrl = 'https://daysof93-cdn.b-cdn.net/meshes/' + filename;
  const res = await fetch(bunnyUrl);

  if (!res.ok) {
    return new Response('Not found', { status: 404 });
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
