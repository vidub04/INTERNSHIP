/*
 * Copyright (c) Microsoft Corporation. All rights reserved. Licensed under the MIT license.
 * See LICENSE in the project root for license information.
 */

/* global console, document, Excel, Office */

document.getElementById("runBtn").onclick = async () => {
  const file = document.getElementById("fileInput").files[0];
  const type = document.getElementById("reportType").value;
  const form = new FormData();
  form.append("file", file);
  form.append("analysis_type", type);

  const res = await fetch("http://localhost:8000/analyze", {
    method: "POST", body: form
  });
  const { summary } = await res.json();

  document.getElementById("output").textContent = summary;
  // Or insert results into Excel via Excel.run(...)
};
