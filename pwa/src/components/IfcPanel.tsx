import { ChangeEvent, FormEvent, useState } from "react";
import { useIfcStore } from "../state/ifc";
import { useAgentStore } from "../modules/agent/state/agentStore";

export default function IfcPanel() {
  const {
    importing,
    exporting,
    importProgress,
    exportProgress,
    progressMessage,
    error,
    lastImport,
    lastExport,
    importIfc,
    exportIfc,
    clearError,
  } = useIfcStore();
  const { connectionState } = useAgentStore();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [exportFilename, setExportFilename] = useState("building.ifc");
  const [useDelta, setUseDelta] = useState(true);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setSelectedFile(file ?? null);
  };

  const handleImport = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedFile) {
      return;
    }
    await importIfc(selectedFile);
    setSelectedFile(null);
  };

  const handleExport = async () => {
    await exportIfc({ filename: exportFilename, delta: useDelta });
  };

  return (
    <section
      className="rounded-xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg shadow-slate-900/40"
      data-testid="panel-ifc"
    >
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-100">IFC Import / Export</h2>
          <p className="text-xs text-slate-400">
            Move building data between IFC files and YAML using the desktop agent. Imports write YAML locally; exports stream the IFC back to your browser.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px] uppercase tracking-wide text-slate-100">
          <span
            className={`rounded-md px-2 py-0.5 ${
              connectionState.status === "connected"
                ? "bg-emerald-500/40"
                : connectionState.status === "connecting"
                ? "bg-sky-500/40"
                : connectionState.status === "error"
                ? "bg-red-500/40"
                : "bg-slate-800"
            }`}
          >
            Agent {connectionState.status}
          </span>
        </div>
      </header>

      {error && (
        <div className="mb-4 rounded-md border border-red-500/50 bg-red-900/30 px-3 py-2 text-xs text-red-200">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => clearError()} className="text-[10px] uppercase tracking-wide">
              Dismiss
            </button>
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <form onSubmit={handleImport} className="space-y-3 rounded-lg border border-slate-800 bg-slate-950/60 p-4 text-xs text-slate-300">
          <h3 className="text-sm font-semibold text-slate-100">Import IFC</h3>
          <p className="text-slate-400">
            Upload an IFC file to generate YAML inside the local repository. The agent parses the file with the Rust IFC processor and writes sanitized output.
          </p>
          <input
            type="file"
            accept=".ifc"
            onChange={handleFileChange}
            className="block w-full text-[11px] text-slate-200 file:mr-4 file:rounded-md file:border file:border-slate-700 file:bg-slate-800 file:px-3 file:py-1 file:text-xs file:font-semibold file:uppercase file:tracking-wide file:text-slate-100 hover:file:border-slate-500 hover:file:bg-slate-700"
          />
          <button
            type="submit"
            disabled={!selectedFile || importing}
            className="rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-100 transition hover:border-slate-500 hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {importing ? "Importing…" : "Import IFC"}
          </button>
          {importing && (
            <div className="space-y-2">
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full bg-sky-500 transition-all duration-300"
                  style={{ width: `${importProgress}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-400">{progressMessage}</p>
            </div>
          )}
          {lastImport && (
            <dl className="space-y-1 rounded border border-slate-800 bg-slate-950/70 p-3">
              <div className="flex justify-between">
                <dt>Building</dt>
                <dd>{lastImport.buildingName}</dd>
              </div>
              <div className="flex justify-between">
                <dt>YAML</dt>
                <dd className="truncate text-sky-300" title={lastImport.yamlPath}>
                  {lastImport.yamlPath}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt>Floors</dt>
                <dd>{lastImport.floors}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Rooms</dt>
                <dd>{lastImport.rooms}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Equipment</dt>
                <dd>{lastImport.equipment}</dd>
              </div>
            </dl>
          )}
        </form>

        <div className="space-y-3 rounded-lg border border-slate-800 bg-slate-950/60 p-4 text-xs text-slate-300">
          <h3 className="text-sm font-semibold text-slate-100">Export IFC</h3>
          <p className="text-slate-400">
            Generate an IFC from the current YAML workspace. Delta exports reuse sync state stored in `.arxos/ifc-sync-state.json`.
          </p>
          <label className="flex items-center gap-2">
            <span className="w-24 text-[11px] uppercase tracking-wide text-slate-400">Filename</span>
            <input
              value={exportFilename}
              onChange={(event) => setExportFilename(event.target.value)}
              className="flex-1 rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-[11px] text-slate-100 focus:border-slate-500 focus:outline-none"
            />
          </label>
          <label className="flex items-center gap-2 text-[11px]">
            <input
              type="checkbox"
              checked={useDelta}
              onChange={(event) => setUseDelta(event.target.checked)}
              className="rounded border border-slate-600 bg-slate-950 text-sky-400 focus:ring-sky-500"
            />
            Use delta export when sync state is available
          </label>
          <button
            type="button"
            disabled={exporting}
            onClick={handleExport}
            className="rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-100 transition hover:border-slate-500 hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {exporting ? "Exporting…" : "Export IFC"}
          </button>
          {exporting && (
            <div className="space-y-2">
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full bg-sky-500 transition-all duration-300"
                  style={{ width: `${exportProgress}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-400">{progressMessage}</p>
            </div>
          )}
          {lastExport && (
            <div className="space-y-1 rounded border border-slate-800 bg-slate-950/70 p-3">
              <p>
                <span className="text-slate-400">File:</span> {lastExport.filename}
              </p>
              <p>
                <span className="text-slate-400">Size:</span> {(lastExport.sizeBytes / 1024).toLocaleString()} KB
              </p>
              <a
                href={lastExport.downloadUrl}
                download
                className="inline-block rounded-md border border-slate-700 bg-slate-800 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-100 transition hover:border-slate-500 hover:bg-slate-700"
              >
                Download IFC
              </a>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
