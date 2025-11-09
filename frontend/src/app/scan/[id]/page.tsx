import ScanDetailClient from './ScanDetailClient';

export default function ScanDetailPage({
  params,
}: {
  params: { id: string };
}) {
  return <ScanDetailClient scanId={params.id} />;
}
