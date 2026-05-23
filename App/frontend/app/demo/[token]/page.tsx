import DemoChat from "./DemoChat";

interface DemoPageProps {
  params: Promise<{ token: string }>;
}

export default async function DemoPage({ params }: DemoPageProps) {
  const { token } = await params;
  return <DemoChat token={token} />;
}
