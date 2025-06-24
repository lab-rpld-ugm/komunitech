document.addEventListener('DOMContentLoaded', function() {
    // Aktifkan semua tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Hilangkan pesan flash setelah beberapa detik
    // setTimeout(function() {
    //     var alerts = document.querySelectorAll('.alert');
    //     alerts.forEach(function(alert) {
    //         var bsAlert = new bootstrap.Alert(alert);
    //         bsAlert.close();
    //     });
    // }, 5000);

    // Animasikan statistik pada halaman beranda
    animateNumbers();

    // Validasi form sisi klien
    setupFormValidation();
});

// Animasi untuk angka-angka statistik
function animateNumbers() {
    const statsElements = document.querySelectorAll('.stat-number');
    
    if (statsElements.length > 0) {
        statsElements.forEach(function(element) {
            const targetVal = parseInt(element.getAttribute('data-value'));
            const duration = 2000; // Durasi dalam milidetik
            const step = targetVal / (duration / 50); // Langkah untuk setiap iterasi
            let current = 0;
            
            const timer = setInterval(function() {
                current += step;
                if (current >= targetVal) {
                    element.textContent = targetVal;
                    clearInterval(timer);
                } else {
                    element.textContent = Math.floor(current);
                }
            }, 50);
        });
    }
}

// Validasi form sisi klien
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

// Handle filter dan pencarian untuk daftar kebutuhan
const filterForm = document.getElementById('filter-form');
if (filterForm) {
    filterForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Di sini bisa ditambahkan kode untuk filter AJAX
        console.log('Filter disubmit');
    });
}

// Tampilkan konfirmasi sebelum melakukan tindakan penting
function confirmAction(message) {
    return confirm(message || 'Apakah Anda yakin?');
}

// Fungsi untuk memperbarui jumlah dukungan tanpa reload halaman
function updateVote(kebutuhanId) {
    // Ini akan diimplementasikan dengan AJAX call ke server
    console.log('Memperbarui dukungan untuk kebutuhan ID:', kebutuhanId);
    
    // Contoh sederhana tanpa AJAX (di implementasi nyata akan menggunakan fetch API)
    const voteCountElement = document.getElementById('vote-count-' + kebutuhanId);
    if (voteCountElement) {
        const currentCount = parseInt(voteCountElement.textContent);
        voteCountElement.textContent = currentCount + 1;
    }
}

// Deteksi scroll dan tambahkan kelas ke navbar
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.classList.add('navbar-scrolled', 'shadow-sm');
        } else {
            navbar.classList.remove('navbar-scrolled', 'shadow-sm');
        }
    }
});

// Fungsi untuk preview gambar yang diupload
function previewImage(input, previewId) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const preview = document.getElementById(previewId);
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
        }
        
        reader.readAsDataURL(input.files[0]);
    }
}