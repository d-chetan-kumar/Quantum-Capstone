export default function EmptyStatePage({ title }: { title: string }) {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">{title}</h1>
      <div className="p-8 border border-dashed border-slate-300 dark:border-slate-700 rounded-lg text-center text-slate-500">
        <p>{title} functionality will be implemented in a future phase.</p>
      </div>
    </div>
  );
}
