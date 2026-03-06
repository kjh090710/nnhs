let selectedStudent = null;
const openedDetails = new Set();

function showBox(elementId, message, type) {
  const box = document.getElementById(elementId);
  box.classList.remove("hidden", "success", "error");
  box.classList.add(type);
  box.innerHTML = message;
}

async function searchStudent() {
  const studentNumber = document.getElementById("studentNumber").value.trim();

  if (!studentNumber) {
    showBox("studentInfo", "학번을 입력하세요.", "error");
    return;
  }

  try {
    const response = await fetch(`/api/student/${studentNumber}`);
    const data = await response.json();

    if (data.success) {
      selectedStudent = data;
      showBox(
        "studentInfo",
        `검색 결과: <strong>${data.student_number}</strong> / <strong>${data.name}</strong>`,
        "success"
      );
    } else {
      selectedStudent = null;
      showBox("studentInfo", data.message, "error");
    }
  } catch (error) {
    selectedStudent = null;
    showBox("studentInfo", "학생 검색 중 오류가 발생했습니다.", "error");
  }
}

async function saveGuidance() {
  const studentNumber = document.getElementById("studentNumber").value.trim();
  const content = document.getElementById("content").value.trim();

  if (!studentNumber) {
    showBox("message", "먼저 학번을 입력하세요.", "error");
    return;
  }

  if (!content) {
    showBox("message", "선도 내용을 입력하세요.", "error");
    return;
  }

  try {
    const response = await fetch("/api/guidance", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        student_number: studentNumber,
        content: content
      })
    });

    const data = await response.json();

    if (data.success) {
      showBox(
        "message",
        `<strong>${data.data.student_name}</strong> 학생의 선도 내용이 저장되었습니다.`,
        "success"
      );

      document.getElementById("content").value = "";

      await loadGuidanceSummary();

      if (openedDetails.has(studentNumber)) {
        await toggleDetail(studentNumber, true);
      }
    } else {
      showBox("message", data.message, "error");
    }
  } catch (error) {
    showBox("message", "선도 내용 저장 중 오류가 발생했습니다.", "error");
  }
}

async function loadGuidanceSummary() {
  const tbody = document.getElementById("summaryTableBody");

  try {
    const response = await fetch("/api/guidance-summary");
    const data = await response.json();

    if (!data.success || data.students.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="4">선도 기록이 있는 학생이 없습니다.</td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = "";

    data.students.forEach(student => {
      const summaryRow = document.createElement("tr");
      summaryRow.innerHTML = `
        <td>${student.student_number}</td>
        <td>${student.student_name}</td>
        <td>${student.guidance_count}회</td>
        <td>
          <button class="detail-btn" onclick="toggleDetail('${student.student_number}')">
            ${openedDetails.has(student.student_number) ? "닫기" : "더보기"}
          </button>
        </td>
      `;
      tbody.appendChild(summaryRow);

      const detailRow = document.createElement("tr");
      detailRow.id = `detail-row-${student.student_number}`;
      detailRow.className = "detail-row";
      detailRow.style.display = openedDetails.has(student.student_number) ? "" : "none";
      detailRow.innerHTML = `
        <td colspan="4">
          <div id="detail-box-${student.student_number}" class="detail-box">
            ${
              openedDetails.has(student.student_number)
                ? "불러오는 중..."
                : "상세 내역이 여기에 표시됩니다."
            }
          </div>
        </td>
      `;
      tbody.appendChild(detailRow);
    });

    for (const studentNumber of openedDetails) {
      await renderStudentDetails(studentNumber);
    }

  } catch (error) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4">학생별 선도 현황을 불러오지 못했습니다.</td>
      </tr>
    `;
  }
}

async function toggleDetail(studentNumber, keepOpen = false) {
  const row = document.getElementById(`detail-row-${studentNumber}`);
  const isOpen = openedDetails.has(studentNumber);

  if (!keepOpen && isOpen) {
    openedDetails.delete(studentNumber);
    if (row) row.style.display = "none";
    await loadGuidanceSummary();
    return;
  }

  openedDetails.add(studentNumber);
  if (row) row.style.display = "";
  await renderStudentDetails(studentNumber);
  await loadGuidanceSummary();
}

async function renderStudentDetails(studentNumber) {
  const box = document.getElementById(`detail-box-${studentNumber}`);
  if (!box) return;

  box.innerHTML = "불러오는 중...";

  try {
    const response = await fetch(`/api/student-guidances/${studentNumber}`);
    const data = await response.json();

    if (!data.success) {
      box.innerHTML = `<div class="detail-empty">${data.message}</div>`;
      return;
    }

    if (data.guidances.length === 0) {
      box.innerHTML = `<div class="detail-empty">선도 내역이 없습니다.</div>`;
      return;
    }

    let html = `
      <div class="detail-header">
        <strong>${data.student_name}</strong> (${data.student_number}) · 총 ${data.guidance_count}회
      </div>
      <div class="detail-list">
    `;

    data.guidances.forEach((item, index) => {
      html += `
        <div class="detail-item">
          <div class="detail-item-top">
            <span class="detail-badge">${data.guidance_count - index}회차</span>
            <span class="detail-date">${item.created_at}</span>
          </div>
          <div class="detail-content">${item.content}</div>
        </div>
      `;
    });

    html += `</div>`;
    box.innerHTML = html;

  } catch (error) {
    box.innerHTML = `<div class="detail-empty">상세 내역을 불러오지 못했습니다.</div>`;
  }
}

async function uploadExcel() {
  const fileInput = document.getElementById("excelFile");
  const file = fileInput.files[0];

  if (!file) {
    showBox("uploadMessage", "엑셀 파일을 선택하세요.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/upload-students-excel", {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    if (data.success) {
      showBox("uploadMessage", data.message, "success");
      fileInput.value = "";
      loadGuidanceSummary();
    } else {
      showBox("uploadMessage", data.message, "error");
    }
  } catch (error) {
    showBox("uploadMessage", "엑셀 업로드 중 오류가 발생했습니다.", "error");
  }
}

loadGuidanceSummary();