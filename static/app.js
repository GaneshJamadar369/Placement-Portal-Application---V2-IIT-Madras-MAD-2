const { createApp } = Vue;

const app = createApp({
    data() {
        return {
            loggedIn: false,
            showLanding: true,
            role: null,
            userName: "",
            authMode: "login",
            errorMsg: "",

            flashMessage: "",
            flashType: "success",

            notifications: [],
            notificationsLoadedOnce: false,
            showNotifications: false,
            toasts: [],
            pollTimer: null,

            form: { role: "student", name: "", email: "", password: "", branch: "", cgpa: "", company_name: "", hr_name: "" },

            // student
            studentTab: "browse",
            drives: [],
            loadingDrives: false,
            applications: [],
            loadingApplications: false,
            profileForm: { branch: "", cgpa: "" },
            resumePath: null,
            resumeFile: null,
            exports: [],

            // company
            companyTab: "status",
            companyProfile: {},
            loadingCompanyProfile: false,
            newDrive: { title: "", description: "", package: "", location: "", eligibility_branch: "", eligibility_min_cgpa: "", deadline: "" },
            myDrives: [],
            loadingMyDrives: false,
            selectedDriveId: null,
            applicants: [],
            loadingApplicants: false,

            // admin
            adminTab: "overview",
            stats: {},
            allCompanies: [],
            loadingCompanies: false,
            companySearch: "",
            companyStatusFilter: "All",
            allDrives: [],
            loadingAdminDrives: false,
            driveSearch: "",
            driveStatusFilter: "All",
            allStudents: [],
            loadingStudents: false,
            studentSearch: ""
        };
    },

    computed: {
        filteredCompanies() {
            if (this.companyStatusFilter === "All") return this.allCompanies;
            return this.allCompanies.filter(c => c.approval_status === this.companyStatusFilter);
        },
        filteredDrives() {
            if (this.driveStatusFilter === "All") return this.allDrives;
            return this.allDrives.filter(d => d.status === this.driveStatusFilter);
        },
        unreadCount() {
            return this.notifications.filter(n => !n.is_read).length;
        }
    },

    mounted() {
        this.checkSession();
    },

    methods: {
        showFlash(message, type = "success") {
            this.flashMessage = message;
            this.flashType = type;
            setTimeout(() => { this.flashMessage = ""; }, 4000);
        },

        showToast(message) {
            const id = Date.now() + Math.random();
            this.toasts.push({ id, message });
            setTimeout(() => {
                this.toasts = this.toasts.filter(t => t.id !== id);
            }, 5000);
        },

        async loadNotifications() {
            const previousIds = new Set(this.notifications.map(n => n.id));
            const latest = await (await fetch("/notifications")).json();

            if (this.notificationsLoadedOnce) {
                const freshOnes = latest.filter(n => !previousIds.has(n.id));
                freshOnes.forEach(n => this.showToast(n.message));
            }

            this.notifications = latest;
            this.notificationsLoadedOnce = true;
        },

        async markNotificationRead(id) {
            await fetch(`/notifications/${id}/read`, { method: "PATCH" });
            const n = this.notifications.find(x => x.id === id);
            if (n) n.is_read = true;
        },

        async markAllNotificationsRead() {
            await fetch("/notifications/read-all", { method: "PATCH" });
            this.notifications.forEach(n => n.is_read = true);
        },

        startPolling() {
            if (this.pollTimer) return;
            this.pollTimer = setInterval(() => {
                this.loadNotifications();
                this.refreshCurrentView();
            }, 8000);
        },

        stopPolling() {
            if (this.pollTimer) {
                clearInterval(this.pollTimer);
                this.pollTimer = null;
            }
        },

        refreshCurrentView() {
            if (this.role === "student") this.loadStudentDashboard();
            if (this.role === "company") {
                this.loadCompanyDashboard();
                if (this.companyTab === "applicants") this.loadApplicants();
            }
            if (this.role === "admin") this.loadAdminDashboard();
        },

        async checkSession() {
            const data = await (await fetch("/me")).json();
            if (data.logged_in) {
                this.loggedIn = true;
                this.showLanding = false;
                this.role = data.role;
                this.userName = data.name;
                this.loadDashboard();
                this.loadNotifications();
                this.startPolling();
            }
        },

        async login() {
            this.errorMsg = "";
            const res = await fetch("/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: this.form.email, password: this.form.password })
            });
            const data = await res.json();
            if (!res.ok) {
                this.errorMsg = data.error;
                return;
            }
            this.loggedIn = true;
            this.role = data.role;
            this.loadDashboard();
            this.loadNotifications();
            this.startPolling();
        },

        async register() {
            this.errorMsg = "";
            const res = await fetch("/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(this.form)
            });
            const data = await res.json();
            if (!res.ok) {
                this.errorMsg = data.error;
                return;
            }
            this.authMode = "login";
            this.errorMsg = "Registered! Please login.";
        },

        async logout() {
            await fetch("/logout", { method: "POST" });
            this.loggedIn = false;
            this.role = null;
            this.showLanding = true;
            this.notifications = [];
            this.stopPolling();
        },

        loadDashboard() {
            if (this.role === "student") this.loadStudentDashboard();
            if (this.role === "company") this.loadCompanyDashboard();
            if (this.role === "admin") this.loadAdminDashboard();
        },

        // ---------- STUDENT ----------

        async loadStudentDashboard() {
            this.loadingDrives = true;
            try {
                this.drives = await (await fetch("/student/drives")).json();
            } finally {
                this.loadingDrives = false;
            }

            this.loadingApplications = true;
            try {
                this.applications = await (await fetch("/student/applications")).json();
            } finally {
                this.loadingApplications = false;
            }

            const profile = await (await fetch("/student/profile")).json();
            this.profileForm.branch = profile.branch;
            this.profileForm.cgpa = profile.cgpa;
            this.resumePath = profile.resume;

            this.exports = await (await fetch("/student/applications/exports")).json();
        },

        async applyToDrive(driveId) {
            const res = await fetch("/student/applications", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ drive_id: driveId })
            });
            const data = await res.json();
            this.showFlash(data.message || data.error, res.ok ? "success" : "danger");
            this.loadStudentDashboard();
        },

        async exportApplications() {
            const res = await fetch("/student/applications/export", { method: "POST" });
            const data = await res.json();
            this.showFlash(data.message || data.error, res.ok ? "success" : "danger");

            if (res.ok) {
                setTimeout(async () => {
                    this.exports = await (await fetch("/student/applications/exports")).json();
                }, 2000);
            }
        },

        async updateProfile() {
            const res = await fetch("/student/profile", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(this.profileForm)
            });
            const data = await res.json();
            this.showFlash(data.message || data.error, res.ok ? "success" : "danger");
        },

        onResumeFileChange(event) {
            this.resumeFile = event.target.files[0] || null;
        },

        async uploadResume() {
            if (!this.resumeFile) {
                this.showFlash("Please choose a file first", "danger");
                return;
            }
            const formData = new FormData();
            formData.append("resume", this.resumeFile);

            const res = await fetch("/student/resume", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            this.showFlash(data.message || data.error, res.ok ? "success" : "danger");
            if (res.ok) this.resumePath = data.path;
        },

        // ---------- COMPANY ----------

        async loadCompanyDashboard() {
            this.loadingCompanyProfile = true;
            try {
                this.companyProfile = await (await fetch("/company/profile")).json();
            } finally {
                this.loadingCompanyProfile = false;
            }
            this.loadMyDrives();
        },

        async loadMyDrives() {
            this.loadingMyDrives = true;
            try {
                this.myDrives = await (await fetch("/company/drives")).json();
            } finally {
                this.loadingMyDrives = false;
            }
        },

        async createDrive() {
            const res = await fetch("/company/drives", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(this.newDrive)
            });
            const data = await res.json();
            this.showFlash(data.message || data.error, res.ok ? "success" : "danger");
            if (res.ok) {
                this.newDrive = { title: "", description: "", package: "", location: "", eligibility_branch: "", eligibility_min_cgpa: "", deadline: "" };
            }
            this.loadMyDrives();
        },

        viewApplicants(driveId) {
            this.selectedDriveId = driveId;
            this.companyTab = "applicants";
            this.loadApplicants();
        },

        async loadApplicants() {
            if (!this.selectedDriveId) return;
            this.loadingApplicants = true;
            try {
                this.applicants = await (await fetch(`/company/drives/${this.selectedDriveId}/applications`)).json();
            } finally {
                this.loadingApplicants = false;
            }
        },

        async setApplicationStatus(applicationId, status) {
            const res = await fetch(`/company/applications/${applicationId}/status`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status })
            });
            const data = await res.json();
            this.showFlash(data.message || data.error, res.ok ? "success" : "danger");
            this.loadApplicants();
        },

        // ---------- ADMIN ----------

        async loadAdminDashboard() {
            this.stats = await (await fetch("/admin/stats")).json();
            this.loadCompanies();
            this.loadAdminDrives();
            this.loadStudents();
        },

        async loadCompanies() {
            this.loadingCompanies = true;
            try {
                const url = this.companySearch ? `/admin/companies?search=${encodeURIComponent(this.companySearch)}` : "/admin/companies";
                this.allCompanies = await (await fetch(url)).json();
            } finally {
                this.loadingCompanies = false;
            }
        },

        async loadAdminDrives() {
            this.loadingAdminDrives = true;
            try {
                const url = this.driveSearch ? `/admin/drives?search=${encodeURIComponent(this.driveSearch)}` : "/admin/drives";
                this.allDrives = await (await fetch(url)).json();
            } finally {
                this.loadingAdminDrives = false;
            }
        },

        async loadStudents() {
            this.loadingStudents = true;
            try {
                const url = this.studentSearch ? `/admin/students?search=${encodeURIComponent(this.studentSearch)}` : "/admin/students";
                this.allStudents = await (await fetch(url)).json();
            } finally {
                this.loadingStudents = false;
            }
        },

        async approveCompany(id) {
            const res = await fetch(`/admin/companies/${id}/approve`, { method: "PATCH" });
            const data = await res.json();
            this.showFlash(data.message || data.error, res.ok ? "success" : "danger");
            this.loadCompanies();
            this.stats = await (await fetch("/admin/stats")).json();
        },
        async rejectCompany(id) {
            const res = await fetch(`/admin/companies/${id}/reject`, { method: "PATCH" });
            const data = await res.json();
            this.showFlash(data.message || data.error, res.ok ? "success" : "danger");
            this.loadCompanies();
        },
        async approveDrive(id) {
            const res = await fetch(`/admin/drives/${id}/approve`, { method: "PATCH" });
            const data = await res.json();
            this.showFlash(data.message || data.error, res.ok ? "success" : "danger");
            this.loadAdminDrives();
            this.stats = await (await fetch("/admin/stats")).json();
        },
        async rejectDrive(id) {
            const res = await fetch(`/admin/drives/${id}/reject`, { method: "PATCH" });
            const data = await res.json();
            this.showFlash(data.message || data.error, res.ok ? "success" : "danger");
            this.loadAdminDrives();
        },

        async setUserStatus(userId, status) {
            const res = await fetch(`/admin/users/${userId}/status`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status })
            });
            const data = await res.json();
            this.showFlash(data.message || data.error, res.ok ? "success" : "danger");
            this.loadStudents();
        }
    }
});

app.component("status-badge", {
    props: ["status"],
    computed: {
        badgeClass() {
            const map = {
                Active: "pp-badge-success",
                Approved: "pp-badge-success",
                Selected: "pp-badge-success",
                Pending: "pp-badge-warning",
                Rejected: "pp-badge-danger",
                Blacklisted: "pp-badge-danger",
                Deactivated: "pp-badge-neutral",
                Closed: "pp-badge-neutral",
                Applied: "pp-badge-info",
                Shortlisted: "pp-badge-primary"
            };
            return map[this.status] || "pp-badge-neutral";
        }
    },
    template: '<span class="pp-badge" :class="badgeClass">{{ status }}</span>'
});

app.mount("#app");
