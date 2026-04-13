<script lang="ts">
  import Router from 'svelte-spa-router';
  import Home from './routes/Home.svelte';
  import Chat from './routes/Chat.svelte';
  import Admin from './routes/Admin.svelte';

  const routes = {
    '/': Home,
    '/chat': Chat,
    '/admin': Admin,
    '*': Home,
  };
</script>

<Router {routes} />
