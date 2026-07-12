const { createApp } = Vue;

createApp({
    data() {
        return {
            loggedIn: false,
            role: null,
            authMode: "login",
            errorMsg: "",
            form: { role: "student", name: "", email: "", password: "", branch: "", cgpa: "", company_name: "", hr_name: "" },

            drives: [],
            applications: [],

            newDrive: { title: "", package: "", eligibility_branch: "", eligibility_min_cgpa: "", deadline: "" },
            myDrives: [],

            stats: {},
            pendingCompanies: [],
            pendingDrives: []
        };
    },

    mounted() {
        this.checkSession();
    },

    methods: {
        async checkSession() {
            // No dedicated "who am I" endpoint yet, so we just show login screen on load.
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
        },

        loadDashboard() {
            if (this.role === "student") this.loadStudentDashboard();
            if (this.role === "company") this.loadCompanyDashboard();
            if (this.role === "admin") this.loadAdminDashboard();
        },

        async loadStudentDashboard() {
            this.drives = await (await fetch("/student/drives")).json();
            this.applications = await (await fetch("/student/applications")).json();
        },

        async applyToDrive(driveId) {
            const res = await fetch("/student/applications", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ drive_id: driveId })
            });
            const data = await res.json();
            alert(data.message || data.error);
            this.loadStudentDashboard();
        },

        async loadCompanyDashboard() {
            this.myDrives = await (await fetch("/company/drives")).json();
        },

        async createDrive() {
            const res = await fetch("/company/drives", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(this.newDrive)
            });
            const data = await res.json();
            alert(data.message || data.error);
            this.loadCompanyDashboard();
        },

        async loadAdminDashboard() {
            this.stats = await (await fetch("/admin/stats")).json();
            this.pendingCompanies = await (await fetch("/admin/companies/pending")).json();
            this.pendingDrives = await (await fetch("/admin/drives/pending")).json();
        },

        async approveCompany(id) {
            await fetch(`/admin/companies/${id}/approve`, { method: "PATCH" });
            this.loadAdminDashboard();
        },
        async rejectCompany(id) {
            await fetch(`/admin/companies/${id}/reject`, { method: "PATCH" });
            this.loadAdminDashboard();
        },
        async approveDrive(id) {
            await fetch(`/admin/drives/${id}/approve`, { method: "PATCH" });
            this.loadAdminDashboard();
        },
        async rejectDrive(id) {
            await fetch(`/admin/drives/${id}/reject`, { method: "PATCH" });
            this.loadAdminDashboard();
        }
    }
}).mount("#app");
