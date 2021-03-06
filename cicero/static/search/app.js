// we put all the js code into an anonymous function
// this is good practice to isolate the namespace
;
(function() {


    // with this we make js less forgiving so that we catch
    // more hidden errors during development
    'use strict';


    function has_markdown_suffix(file_name) {
        return file_name.path.endsWith('.md') || file_name.path.endsWith('.mkd')
    }


    var app = new Vue({
        el: '#app',
        data: {
            user: '',
            repo: '',
            repos: [],
            branch: '',
            branches: [],
            file: '',
            files: [],
            files_loaded: false,
            link: '',
            source_link: '',
        },
        watch: {
            user: function(new_user, old_user) {
                this.debounced_load_repos()
            },
            repo: function(new_repo, old_repo) {
                this.load_branches()
            },
            branch: function(new_branch, old_branch) {
                this.load_files()
            },
            file: function(new_file, old_file) {
                this.update_links()
            },
        },
        created: function() {
            // https://lodash.com/docs#debounce
            this.debounced_load_repos = _.debounce(this.load_repos, 500)
        },
        methods: {
            load_repos: function() {
                var vm = this
                axios.get('https://api.github.com/users/' + this.user + '/repos?per_page=1000')
                    .then(function(response) {
                        vm.repos = response.data
                    })
            },
            load_branches: function() {
                var vm = this
                axios.get('https://api.github.com/repos/' + this.user + '/' + this.repo + '/branches')
                    .then(function(response) {
                        vm.branches = response.data
                    })
            },
            load_files: function() {
                var vm = this
                axios.get('https://api.github.com/repos/' + vm.user + '/' + vm.repo + '/git/refs/heads/' + vm.branch)
                    .then(function(response) {
                        var sha = response.data.object.sha
                        axios.get('https://api.github.com/repos/' + vm.user + '/' + vm.repo + '/git/trees/' + sha +
                                '?recursive=1')
                            .then(function(response2) {
                                vm.files = response2.data.tree.filter(has_markdown_suffix);
                                vm.files_loaded = true;
                            })
                    })
            },
            update_links: function() {
                var vm = this
                vm.link = '/v2/remark/github/' + vm.user + '/' + vm.repo + '/' + vm.branch + '/' + vm.file + '/'
                vm.source_link = 'https://github.com/' + vm.user + '/' + vm.repo + '/blob/' + vm.branch + '/' + vm.file
            },
        },
        delimiters: ['[[', ']]']
    })


    // close the anonymous function
})();